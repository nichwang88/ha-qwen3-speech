"""Qwen3 Speech integration for Home Assistant (TTS & STT)."""
from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
import time

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import get_url

from .const import (
    AUTO_INSTRUCTIONS,
    CONF_INSTRUCTIONS,
    CONF_VOICE,
    DASHSCOPE_API_URL,
    DEFAULT_EMOTION,
    DOMAIN,
    pick_emotion,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TTS, Platform.STT]

SERVICE_BROADCAST = "broadcast"
BROADCAST_FILE = "qwen3_broadcast.mp3"

# qwen text model (HTTP) used to judge the daily-quote emotion. Tried in order.
LLM_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
LLM_MODELS = ("qwen-flash", "qwen-turbo", "qwen-plus")
QUOTE_MARKER = "一言"          # the sentence after this marker is the daily quote
PAUSE_S = 0.25                 # silence inserted between segments

BROADCAST_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Required("media_player_entity_id"): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Optional("voice"): cv.string,
        vol.Optional("instructions", default=AUTO_INSTRUCTIONS): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Qwen3 Speech from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_BROADCAST):
        hass.services.async_register(
            DOMAIN, SERVICE_BROADCAST, _make_broadcast_handler(hass),
            schema=BROADCAST_SCHEMA,
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


# --- broadcast service: per-segment emotion + LLM-judged daily quote ---------
# Long instruct/emotion synthesis is slow and times out HA's lazy TTS / pyatv.
# This service renders the whole clip to a file first (offline). With
# instructions="auto" it splits the text into sentences, picks an emotion per
# segment (the daily quote gets an LLM-judged tone), synthesises them
# concurrently and concatenates with short pauses, then plays the finished file.

def _get_tts_entity(hass: HomeAssistant):
    for data in hass.data.get(DOMAIN, {}).values():
        if isinstance(data, dict) and data.get("tts_entity"):
            return data["tts_entity"]
    return None


def _write_file(path: str, data: bytes) -> None:
    with open(path, "wb") as handle:
        handle.write(data)


async def _synth_wav(session, api_key, model, voice, text, instructions) -> bytes | None:
    """Synthesise one segment -> WAV bytes (no transcode). Retries on throttling."""
    payload = {"model": model, "input": {"text": text, "voice": voice,
                                         "language_type": "Chinese"}}
    if instructions:
        payload["input"]["instructions"] = instructions
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            async with asyncio.timeout(40):
                async with session.post(DASHSCOPE_API_URL, json=payload, headers=headers) as r:
                    data = await r.json()
                url = data.get("output", {}).get("audio", {}).get("url")
                if url:
                    async with session.get(url) as ar:
                        return await ar.read()
                if "Throttling" in str(data.get("code", "")) and attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                _LOGGER.error("broadcast: no audio url for segment: %s", str(data)[:200])
                return None
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("broadcast: segment synth failed: %s", err)
            return None
    return None


async def _llm_quote_emotion(session, api_key, quote: str) -> str:
    """Ask a qwen text model for a fitting tone instruction for the quote."""
    prompt = (
        "下面是一句『每日一言』。请用一句简短的中文语气指令（不超过20字），"
        "描述朗读它时最合适的情感语气，例如『用温暖、充满希望的语气说话』。"
        "只输出这句指令，不要解释或引号。\n一言：「%s」" % quote
    )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for model in LLM_MODELS:
        payload = {
            "model": model,
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"result_format": "message"},
        }
        try:
            async with asyncio.timeout(15):
                async with session.post(LLM_URL, json=payload, headers=headers) as r:
                    data = await r.json()
            text = (
                data.get("output", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            ).strip().strip("「」\"' 。")
            if text and len(text) <= 40:
                _LOGGER.debug("broadcast: LLM(%s) quote emotion: %s", model, text)
                return text
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("broadcast: LLM %s failed: %s", model, err)
            continue
    return DEFAULT_EMOTION


def _make_broadcast_handler(hass: HomeAssistant):
    async def _handle(call: ServiceCall) -> None:
        entity = _get_tts_entity(hass)
        if entity is None:
            _LOGGER.error("qwen3_speech.broadcast: TTS entity not available")
            return

        message = call.data["message"]
        voice = call.data.get("voice") or entity._default_voice  # noqa: SLF001
        instructions = (call.data.get("instructions") or AUTO_INSTRUCTIONS).strip()
        api_key = entity._api_key      # noqa: SLF001
        model = entity._tts_model      # noqa: SLF001
        is_instruct = entity._is_instruct_model  # noqa: SLF001
        session = async_get_clientsession(hass)

        audio = await _build_audio(
            session, api_key, model, voice, is_instruct, message, instructions
        )
        if not audio:
            return

        www = hass.config.path("www")
        await hass.async_add_executor_job(lambda: os.makedirs(www, exist_ok=True))
        out_path = os.path.join(www, BROADCAST_FILE)
        await hass.async_add_executor_job(_write_file, out_path, audio)

        try:
            base = get_url(hass, prefer_internal=True, allow_external=True)
        except Exception:  # noqa: BLE001
            base = hass.config.internal_url or ""
        url = f"{base}/local/{BROADCAST_FILE}?v={int(time.time())}"

        await hass.services.async_call(
            "media_player", "play_media",
            {
                "entity_id": call.data["media_player_entity_id"],
                "media_content_id": url,
                "media_content_type": "music",
            },
            blocking=False,
        )
        _LOGGER.debug("qwen3_speech.broadcast: playing %s", url)

    async def _build_audio(session, api_key, model, voice, is_instruct, message, instructions):
        """Return final HomePod-safe MP3 bytes for the message."""
        auto = is_instruct and instructions.lower() == AUTO_INSTRUCTIONS
        fixed = instructions if (is_instruct and not auto) else ""

        if not auto:
            # whole message, single (or no) emotion
            wav = await _synth_wav(session, api_key, model, voice, message, fixed)
            if not wav:
                return None
            return await _to_homepod_mp3(hass, [wav])

        # per-segment emotion; daily quote judged by LLM
        segs = [s.strip() for s in re.split(r"(?<=[。！？!?])", message) if s.strip()]
        if not segs:
            segs = [message]
        quote_idx = next(
            (i + 1 for i, s in enumerate(segs) if QUOTE_MARKER in s and i + 1 < len(segs)),
            None,
        )

        # Sequential synthesis: the instruct model rate-limits concurrent calls.
        wavs = []
        for i, seg in enumerate(segs):
            if i == quote_idx:
                instr = await _llm_quote_emotion(session, api_key, seg)
            else:
                instr = pick_emotion(seg)
            wav = await _synth_wav(session, api_key, model, voice, seg, instr)
            if wav:
                wavs.append(wav)
        if not wavs:
            return None
        return await _to_homepod_mp3(hass, wavs)

    return _handle


async def _to_homepod_mp3(hass: HomeAssistant, wavs: list[bytes]) -> bytes | None:
    """Concat WAV segments (with pauses) -> HomePod-safe mono MP3 via ffmpeg."""
    tmpdir = await hass.async_add_executor_job(tempfile.mkdtemp)
    try:
        files = []
        for i, w in enumerate(wavs):
            fp = os.path.join(tmpdir, f"s{i}.wav")
            await hass.async_add_executor_job(_write_file, fp, w)
            files.append(fp)
        n = len(files)
        inputs: list[str] = []
        for fp in files:
            inputs += ["-i", fp]
        if n == 1:
            fc = "[0:a]aresample=24000[o]"
        else:
            fc = ";".join(f"[{i}:a]apad=pad_dur={PAUSE_S}[a{i}]" for i in range(n))
            fc += (
                ";" + "".join(f"[a{i}]" for i in range(n))
                + f"concat=n={n}:v=0:a=1[o]"
            )
        args = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", *inputs,
            "-filter_complex", fc, "-map", "[o]", "-ac", "1", "-ar", "24000",
            "-map_metadata", "-1", "-id3v2_version", "0", "-write_xing", "0",
            "-codec:a", "libmp3lame", "-b:a", "64k", "-f", "mp3", "pipe:1",
        ]
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        if proc.returncode == 0 and out:
            return out
        _LOGGER.error("broadcast: ffmpeg failed (rc=%s): %s",
                      proc.returncode, err.decode("utf-8", "ignore")[:200])
        return None
    finally:
        def _cleanup():
            for name in os.listdir(tmpdir):
                os.unlink(os.path.join(tmpdir, name))
            os.rmdir(tmpdir)
        try:
            await hass.async_add_executor_job(_cleanup)
        except OSError:
            pass
