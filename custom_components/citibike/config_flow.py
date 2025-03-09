"""Config flow for Citibike integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import aiohttp

from .const import DOMAIN, CONF_STATIONID, CONF_SENSORNAME, STATION_INFO_URL

_LOGGER = logging.getLogger(__name__)


class CitibikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Citibike."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config: dict = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._config = {
                CONF_STATIONID: user_input[CONF_STATIONID],
                CONF_SENSORNAME: user_input.get(CONF_SENSORNAME, ""),
            }

            await self.async_set_unique_id(user_input[CONF_SENSORNAME].lower())
            self._abort_if_unique_id_configured()

            if not (errors := await self._async_try_connect()):
                return self.async_create_entry(
                    title=user_input[CONF_SENSORNAME] or user_input[CONF_STATIONID],
                    data=self._config,
                )

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATIONID, default=user_input.get(CONF_STATIONID, "")
                    ): str,
                    vol.Optional(
                        CONF_SENSORNAME, default=user_input.get(CONF_SENSORNAME, "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def _async_try_connect(self) -> dict[str, str]:
        """Try to connect to the Citibike API and validate the station ID."""
        async with aiohttp.ClientSession() as session:
            async with session.get(STATION_INFO_URL) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Invalid response from station info API: %s", response.status
                    )
                    return {"base": "cannot_connect"}

                data = await response.json()
                station_id = self._config[CONF_STATIONID]
                if not any(
                    station["short_name"] == station_id
                    for station in data["data"]["stations"]
                ):
                    _LOGGER.debug(
                        "Station ID %s not found in station info data", station_id
                    )
                    return {CONF_STATIONID: "invalid_station_id"}

        return {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return CitibikeOptionsFlowHandler(config_entry)


class CitibikeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Citibike options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Citibike options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> dict:
        """Manage the options."""
        if user_input:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_STATIONID,
                    default=self.config_entry.options.get(CONF_STATIONID, ""),
                ): str,
                vol.Optional(
                    CONF_SENSORNAME,
                    default=self.config_entry.options.get(CONF_SENSORNAME, ""),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
