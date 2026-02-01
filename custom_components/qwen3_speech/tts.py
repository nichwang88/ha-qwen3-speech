"""Support for Qwen3 TTS speech service via DashScope API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.components.tts import TextToSpeechEntity, TtsAudioType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_VOICE,
    DASHSCOPE_API_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_VOICE,
    DOMAIN,
    LANGUAGE_MAP,
    SUPPORT_LANGUAGES,
    TTS_MAX_CHARS,
    TTS_MODEL,
    VOICES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Qwen3 TTS platform via config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    default_voice = config_entry.data.get(CONF_VOICE, DEFAULT_VOICE)
    async_add_entities([Qwen3TTSEntity(hass, api_key, default_voice, config_entry)])


class Qwen3TTSEntity(TextToSpeechEntity):
    """Qwen3 TTS entity using DashScope API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        default_voice: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize Qwen3 TTS entity."""
        self.hass = hass
        self._api_key = api_key
        self._default_voice = default_voice
        self._attr_name = "Qwen3 TTS"
        self._attr_unique_id = f"{DOMAIN}_tts_{config_entry.entry_id}"

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "zh"

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options."""
        return [CONF_VOICE]

    @property
    def default_options(self) -> dict[str, Any]:
        """Return default options."""
        return {CONF_VOICE: self._default_voice}

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS audio from DashScope API."""
        voice = options.get(CONF_VOICE, self._default_voice)
        language_type = LANGUAGE_MAP.get(language, DEFAULT_LANGUAGE)

        if len(message) > TTS_MAX_CHARS:
            _LOGGER.warning(
                "Text length %d exceeds limit %d, truncating",
                len(message),
                TTS_MAX_CHARS,
            )
            message = message[:TTS_MAX_CHARS]

        payload = {
            "model": TTS_MODEL,
            "input": {
                "text": message,
                "voice": voice,
                "language_type": language_type,
            },
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        session = async_get_clientsession(self.hass)

        try:
            # Step 1: Request TTS synthesis
            async with asyncio.timeout(30):
                async with session.post(
                    DASHSCOPE_API_URL, json=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "TTS API request failed (status %s): %s",
                            response.status,
                            error_text,
                        )
                        return None, None

                    data = await response.json()

            # Extract audio URL from response
            audio_url = data.get("output", {}).get("audio", {}).get("url")
            if not audio_url:
                _LOGGER.error("No audio URL in TTS response: %s", data)
                return None, None

            # Step 2: Download audio file
            async with asyncio.timeout(30):
                async with session.get(audio_url) as audio_response:
                    if audio_response.status != 200:
                        _LOGGER.error(
                            "Failed to download audio (status %s)",
                            audio_response.status,
                        )
                        return None, None

                    audio_data = await audio_response.read()
                    if not audio_data:
                        _LOGGER.error("Received empty audio data")
                        return None, None

                    # Detect format from Content-Type or default to wav
                    content_type = audio_response.headers.get("Content-Type", "")
                    if "mp3" in content_type or "mpeg" in content_type:
                        audio_format = "mp3"
                    elif "opus" in content_type or "ogg" in content_type:
                        audio_format = "ogg"
                    else:
                        audio_format = "wav"

                    _LOGGER.debug(
                        "TTS audio received: %d bytes, format=%s, voice=%s",
                        len(audio_data),
                        audio_format,
                        voice,
                    )
                    return audio_format, audio_data

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during TTS request")
            return None, None
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error during TTS request: %s", err)
            return None, None
