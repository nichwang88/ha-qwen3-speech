"""Config flow for Qwen3 Speech integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_SPEED,
    CONF_STT_MODEL,
    CONF_TTS_MODEL,
    CONF_VOICE,
    DASHSCOPE_API_URL,
    DEFAULT_SPEED,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    DOMAIN,
    MAX_SPEED,
    MIN_SPEED,
    VOICES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_TTS_MODEL, default=DEFAULT_TTS_MODEL): str,
        vol.Optional(CONF_STT_MODEL, default=DEFAULT_STT_MODEL): str,
        vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(VOICES),
        vol.Optional(CONF_SPEED, default=DEFAULT_SPEED): vol.All(
            vol.Coerce(float), vol.Range(min=MIN_SPEED, max=MAX_SPEED)
        ),
    }
)


async def _validate_api_key(
    hass: HomeAssistant, api_key: str, tts_model: str, voice: str
) -> None:
    """Validate API key by making a test TTS call."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": tts_model,
        "input": {
            "text": "test",
            "voice": voice,
            "language_type": "Auto",
        },
    }
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(15):
            async with session.post(
                DASHSCOPE_API_URL, json=payload, headers=headers
            ) as response:
                if response.status == 401:
                    raise InvalidAuth("Invalid API key")
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API validation failed: %s", error_text)
                    raise CannotConnect(f"API returned status {response.status}")
                result = await response.json()
                if "output" not in result:
                    raise CannotConnect("Unexpected API response format")
    except asyncio.TimeoutError as err:
        raise CannotConnect("Timeout connecting to DashScope API") from err
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Error connecting to API: {err}") from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Qwen3 Speech."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_api_key(
                    self.hass,
                    user_input[CONF_API_KEY],
                    user_input.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL),
                    user_input.get(CONF_VOICE, DEFAULT_VOICE),
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"qwen3_speech_{user_input[CONF_API_KEY][-8:]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Qwen3 Speech", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Qwen3 Speech."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            tts_model = user_input.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL)
            voice = user_input.get(CONF_VOICE, DEFAULT_VOICE)

            try:
                await _validate_api_key(self.hass, api_key, tts_model, voice)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Update entry data with all new values
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, **user_input},
                )
                return self.async_create_entry(data={})

        # Build schema with current values as defaults
        current = self._config_entry.data
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=current.get(CONF_API_KEY, ""),
                ): str,
                vol.Optional(
                    CONF_TTS_MODEL,
                    default=current.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL),
                ): str,
                vol.Optional(
                    CONF_STT_MODEL,
                    default=current.get(CONF_STT_MODEL, DEFAULT_STT_MODEL),
                ): str,
                vol.Optional(
                    CONF_VOICE,
                    default=current.get(CONF_VOICE, DEFAULT_VOICE),
                ): vol.In(VOICES),
                vol.Optional(
                    CONF_SPEED,
                    default=current.get(CONF_SPEED, DEFAULT_SPEED),
                ): vol.All(
                    vol.Coerce(float), vol.Range(min=MIN_SPEED, max=MAX_SPEED)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate invalid authentication."""
