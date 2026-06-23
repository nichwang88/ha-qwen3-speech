"""Qwen3 Speech integration for Home Assistant (TTS & STT)."""
from __future__ import annotations

import logging
import os
import time

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.network import get_url

from .const import AUTO_INSTRUCTIONS, CONF_INSTRUCTIONS, CONF_VOICE, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TTS, Platform.STT]

SERVICE_BROADCAST = "broadcast"
BROADCAST_FILE = "qwen3_broadcast.mp3"

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


# --- broadcast service ---
# Synthesises the whole clip to a file first (offline, with emotion), then plays
# the finished file. Long instruct/emotion clips are too slow for HA's lazy TTS
# and time out pyatv's stream reader; pre-rendering to a static file avoids that.

def _get_tts_entity(hass: HomeAssistant):
    for data in hass.data.get(DOMAIN, {}).values():
        if isinstance(data, dict) and data.get("tts_entity"):
            return data["tts_entity"]
    return None


def _write_file(path: str, data: bytes) -> None:
    with open(path, "wb") as handle:
        handle.write(data)


def _make_broadcast_handler(hass: HomeAssistant):
    async def _handle(call: ServiceCall) -> None:
        entity = _get_tts_entity(hass)
        if entity is None:
            _LOGGER.error("qwen3_speech.broadcast: TTS entity not available")
            return

        options: dict = {
            CONF_INSTRUCTIONS: call.data.get("instructions", AUTO_INSTRUCTIONS)
        }
        if call.data.get("voice"):
            options[CONF_VOICE] = call.data["voice"]

        # async_get_tts_audio does synthesis (+ emotion) + the HomePod-safe
        # MP3 transcode; runs here with no media player attached, so no timeout.
        _fmt, audio = await entity.async_get_tts_audio(
            call.data["message"], "zh", options
        )
        if not audio:
            _LOGGER.error("qwen3_speech.broadcast: synthesis returned no audio")
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

    return _handle
