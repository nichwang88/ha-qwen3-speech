"""Support for Qwen3 ASR speech-to-text service via DashScope API."""
from __future__ import annotations

import asyncio
import base64
import logging
from collections.abc import AsyncIterable

import aiohttp

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_STT_MODEL,
    DASHSCOPE_API_URL,
    DEFAULT_STT_MODEL,
    DOMAIN,
    LANGUAGE_MAP,
    SUPPORT_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)

# Audio format to MIME type mapping
MIME_MAP = {
    AudioFormats.WAV: "audio/wav",
    AudioFormats.OGG: "audio/ogg",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Qwen3 STT platform via config entry."""
    async_add_entities([Qwen3STTEntity(hass, config_entry)])


class Qwen3STTEntity(SpeechToTextEntity):
    """Qwen3 ASR speech-to-text entity using DashScope API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize Qwen3 STT entity."""
        self.hass = hass
        self._entry = config_entry
        self._attr_name = "Qwen3 STT"
        self._attr_unique_id = f"{DOMAIN}_stt_{config_entry.entry_id}"

    @property
    def _api_key(self) -> str:
        return self._entry.data[CONF_API_KEY]

    @property
    def _stt_model(self) -> str:
        return self._entry.data.get(CONF_STT_MODEL, DEFAULT_STT_MODEL)

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000, AudioSampleRates.SAMPLERATE_44100]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO, AudioChannels.CHANNEL_STEREO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to STT service."""
        # Collect all audio data from the stream
        audio_chunks: list[bytes] = []
        async for chunk in stream:
            audio_chunks.append(chunk)

        audio_data = b"".join(audio_chunks)
        if not audio_data:
            _LOGGER.error("Received empty audio stream")
            return SpeechResult("", SpeechResultState.ERROR)

        _LOGGER.debug(
            "Processing audio: %d bytes, format=%s, language=%s",
            len(audio_data),
            metadata.format,
            metadata.language,
        )

        # Base64 encode audio data
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        mime_type = MIME_MAP.get(metadata.format, "audio/wav")
        audio_uri = f"data:{mime_type};base64,{audio_b64}"

        # Map HA language code to ASR language hint
        language_hint = metadata.language if metadata.language in LANGUAGE_MAP else "zh"

        payload = {
            "model": self._stt_model,
            "input": {
                "messages": [
                    {"role": "system", "content": [{"text": ""}]},
                    {"role": "user", "content": [{"audio": audio_uri}]},
                ]
            },
            "parameters": {
                "asr_options": {
                    "enable_itn": True,
                    "language": language_hint,
                }
            },
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        session = async_get_clientsession(self.hass)

        try:
            async with asyncio.timeout(60):
                async with session.post(
                    DASHSCOPE_API_URL, json=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "ASR API request failed (status %s): %s",
                            response.status,
                            error_text,
                        )
                        return SpeechResult("", SpeechResultState.ERROR)

                    data = await response.json()

            # Extract recognized text from response
            choices = data.get("output", {}).get("choices", [])
            if not choices:
                _LOGGER.error("No choices in ASR response: %s", data)
                return SpeechResult("", SpeechResultState.ERROR)

            content = choices[0].get("message", {}).get("content", [])
            if not content:
                _LOGGER.error("No content in ASR response: %s", data)
                return SpeechResult("", SpeechResultState.ERROR)

            text = content[0].get("text", "")
            if not text:
                _LOGGER.warning("Empty text in ASR response")
                return SpeechResult("", SpeechResultState.ERROR)

            _LOGGER.debug("ASR result: %s", text)
            return SpeechResult(text, SpeechResultState.SUCCESS)

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during ASR request")
            return SpeechResult("", SpeechResultState.ERROR)
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error during ASR request: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
