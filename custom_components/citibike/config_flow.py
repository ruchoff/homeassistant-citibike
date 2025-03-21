"""Config flow for Citibike integration."""

import logging
from typing import Any

import voluptuous as vol
from haversine import haversine

from .graphql_queries.get_init_station_query import (
    GET_INIT_STATION_QUERY,
)
from .graphql_requests import fetch_graphql_data
from homeassistant import config_entries
from homeassistant.core import callback, HomeAssistant

from .const import (
    CONF_STATIONID,
    DOMAIN,
    NetworkGraphQLEndpoints,
    NetworkNames,
    NetworkRegion,
)

_LOGGER = logging.getLogger(__name__)


class CitibikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Citibike."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config: dict = {}
        self._stations: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self._config["network"] = user_input["network"]
            return await self.async_step_select_station()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("network"): vol.In(
                        [network.value for network in NetworkNames]
                    ),
                }
            ),
        )

    async def async_step_select_station(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the step to select a station."""
        errors = {}

        if user_input is not None:
            self._config[CONF_STATIONID] = user_input[CONF_STATIONID]

            # Check if the station ID is already configured
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_STATIONID) == user_input[CONF_STATIONID]:
                    errors["base"] = "already_configured"
                    break

            # Set unique ID for the sensor name
            await self.async_set_unique_id(
                f"{self._config['network'].lower()}_{user_input[CONF_STATIONID].lower()}"
            )
            self._abort_if_unique_id_configured()

            if not errors:
                return self.async_create_entry(
                    title=f"{self._config['network']} {user_input[CONF_STATIONID]}",
                    data=self._config,
                )

        # Fetch stations if not already fetched
        if not self._stations:
            errors = await self._async_fetch_stations()

        if errors:
            return self.async_show_form(
                step_id="select_station",
                data_schema=vol.Schema({}),
                errors=errors,
            )

        # Get home zone coordinates
        home_zone = self.hass.states.get("zone.home")
        home_lat = home_zone.attributes["latitude"]
        home_lon = home_zone.attributes["longitude"]

        # Calculate distance to home zone and sort stations
        for station in self._stations:
            station_lat = station["location"]["lat"]
            station_lon = station["location"]["lng"]
            station["distance"] = haversine(
                (home_lat, home_lon), (station_lat, station_lon)
            )

        self._stations.sort(key=lambda x: x["distance"])

        # Create a dropdown list of stations
        station_options = {
            station["stationName"]: station["stationName"] for station in self._stations
        }

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATIONID): vol.In(station_options),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CitibikeOptionsFlowHandler(config_entry)

    async def _async_fetch_stations(self) -> dict[str, str]:
        """Fetch stations from the Citibike GraphQL API asynchronously."""
        network = NetworkNames(self._config.get("network"))
        endpoint = NetworkGraphQLEndpoints[network.name].value
        region_code = NetworkRegion[network.name].value

        query = {
            "query": GET_INIT_STATION_QUERY,
            "variables": {
                "input": {"regionCode": region_code, "rideablePageLimit": 1000}
            },
        }

        data = await fetch_graphql_data(endpoint, query)

        if data.get("base") == "cannot_connect":
            return {"base": "cannot_connect"}

        self._stations = data["data"]["supply"]["stations"]
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
