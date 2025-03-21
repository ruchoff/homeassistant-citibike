"""Config flow for Citibike integration."""

from datetime import timedelta
import logging
from typing import ClassVar

from haversine import haversine
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .cache import StationCache
from .const import (
    CONF_STATIONID,
    DOMAIN,
    NetworkGraphQLEndpoints,
    NetworkNames,
    NetworkRegion,
)
from .graphql_queries.get_init_station_query import GET_INIT_STATION_QUERY
from .graphql_requests import fetch_graphql_data

_LOGGER = logging.getLogger(__name__)


class CitibikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Citibike."""

    # Class level cache configuration
    _stations_cache: ClassVar[dict[str, StationCache]] = {}
    STATION_CACHE_TIMEOUT: ClassVar[timedelta] = timedelta(hours=6)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config: dict = {}
        self._stations: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step to select a network."""
        _LOGGER.debug("Starting user step to select a network")
        if user_input is not None:
            self._config["network"] = user_input["network"]
            _LOGGER.debug("Network selected: %s", user_input["network"])
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
        self, user_input: dict[str, any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the step to select a station within the selected network."""
        _LOGGER.debug("Starting step to select a station")
        errors = {}

        if user_input is not None:
            self._config[CONF_STATIONID] = user_input[CONF_STATIONID]
            _LOGGER.debug("Station selected: %s", user_input[CONF_STATIONID])

            # Check if the station ID is already configured
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_STATIONID) == user_input[CONF_STATIONID]:
                    errors["base"] = "already_configured"
                    _LOGGER.debug(
                        "Station ID %s is already configured",
                        user_input[CONF_STATIONID],
                    )
                    break

            # Set unique ID for the sensor name
            await self.async_set_unique_id(
                f"{self._config['network'].lower()}_{user_input[CONF_STATIONID].lower()}"
            )
            self._abort_if_unique_id_configured()

            if not errors:
                _LOGGER.debug(
                    "Creating entry for network %s and station %s",
                    self._config["network"],
                    user_input[CONF_STATIONID],
                )
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
        network_name = network.name

        # Check station cache
        if cached_data := StationCache.get_cached_data(network_name):
            self._stations = cached_data
            return {}

        _LOGGER.debug("[API] Fetching station list for network %s", network_name)
        region_code = NetworkRegion[network_name].value

        query = {
            "query": GET_INIT_STATION_QUERY,
            "variables": {"input": {"regionCode": region_code}},
        }

        data = await fetch_graphql_data(NetworkGraphQLEndpoints[network_name], query)

        if data.get("base") == "cannot_connect":
            _LOGGER.warning("[API] Connection failed for network %s", network_name)
            return {"base": "cannot_connect"}

        self._stations = data["data"]["supply"]["stations"]
        StationCache.update_cache(network_name, self._stations)
        _LOGGER.debug(
            "[Config] Found %d stations for network %s",
            len(self._stations),
            network_name,
        )

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
