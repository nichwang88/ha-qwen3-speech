"""Config flow for Qwen3 Speech integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_VOICE,
    DASHSCOPE_API_URL,
    DEFAULT_VOICE,
    DOMAIN,
    TTS_MODEL,
    VOICES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(VOICES),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input by making a test API call."""
    api_key = data[CONF_API_KEY]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TTS_MODEL,
        "input": {
            "text": "test",
            "voice": data.get(CONF_VOICE, DEFAULT_VOICE),
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
                    raise CannotConnect(
                        f"API returned status {response.status}"
                    )
                result = await response.json()
                if "output" not in result:
                    raise CannotConnect("Unexpected API response format")
    except asyncio.TimeoutError as err:
        raise CannotConnect("Timeout connecting to DashScope API") from err
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Error connecting to API: {err}") from err

    return {"title": "Qwen3 Speech"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Qwen3 Speech."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Use a hash of the API key as unique ID
                await self.async_set_unique_id(
                    f"qwen3_speech_{user_input[CONF_API_KEY][-8:]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate invalid authentication."""
