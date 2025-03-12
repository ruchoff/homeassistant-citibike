"""Config flow for Citibike integration."""

import logging
from typing import Any

import voluptuous as vol

from config.custom_components.citibike.graphql_queries.get_station_id_query import (
    GET_STATION_ID_QUERY,
)
from config.custom_components.citibike.graphql_requests import fetch_graphql_data
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_STATIONID, DOMAIN

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
            }

            # Check if the station ID is already configured
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_STATIONID) == user_input[CONF_STATIONID]:
                    errors["base"] = "already_configured"
                    break

            # Set unique ID for the sensor name
            await self.async_set_unique_id(user_input[CONF_STATIONID].lower())
            self._abort_if_unique_id_configured()

            if not errors:
                if not (errors := await self._async_try_connect()):
                    return self.async_create_entry(
                        title=user_input[CONF_STATIONID],
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
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CitibikeOptionsFlowHandler(config_entry)

    async def _async_try_connect(self) -> dict[str, str]:
        """Try to connect to the Citibike GraphQL API and validate the station ID asynchronously."""

        # Fetch data using the reusable GraphQL request function
        data = await fetch_graphql_data(GET_STATION_ID_QUERY)

        if data.get("base") == "cannot_connect":
            return {"base": "cannot_connect"}

        # Filter stations by siteId
        station_id = self._config[CONF_STATIONID]
        filtered_data = [
            station
            for station in data["data"]["supply"]["stations"]
            if station["siteId"] == station_id
        ]

        # If no station with the given siteId, return an invalid station ID error
        if not filtered_data:
            _LOGGER.debug("Station ID %s not found in supply data", station_id)
            return {CONF_STATIONID: "invalid_station_id"}

        return {}


class CitibikeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Citibike options."""

    def __init__(self, config_entry) -> None:
        """Initialize the options flow handler."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init")
