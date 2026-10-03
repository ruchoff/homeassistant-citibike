"""Config flow for Citibike integration."""

from datetime import timedelta
import logging
from typing import ClassVar

from haversine import haversine
import voluptuous as vol

from homeassistant import config_entries

from .cache import StationCache
from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
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

    VERSION = 1
    MINOR_VERSION = 2

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
        errors = {}

        if user_input is not None:
            self._config["network"] = user_input["network"]
            _LOGGER.debug("Network selected: %s", user_input["network"])

            errors = await self._async_fetch_stations()
            if not errors:
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
            errors=errors,
        )

    async def async_step_select_station(
        self, user_input: dict[str, any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the step to select a station within the selected network."""
        _LOGGER.debug("Starting step to select a station")

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            station_name = next(
                station["stationName"]
                for station in self._stations
                if station["stationId"] == station_id
            )
            self._config[CONF_STATION_ID] = station_id
            self._config[CONF_STATION_NAME] = station_name
            _LOGGER.debug("Station selected: %s (%s)", station_name, station_id)

            network = NetworkNames(self._config["network"])
            await self.async_set_unique_id(f"{network.name.lower()}_{station_id}")
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                "Creating entry for network %s and station %s",
                self._config["network"],
                station_name,
            )
            return self.async_create_entry(
                title=f"{self._config['network']} {station_name}",
                data=self._config,
            )

        # Calculate distance to home and sort stations
        home = (self.hass.config.latitude, self.hass.config.longitude)
        for station in self._stations:
            station_lat = station["location"]["lat"]
            station_lon = station["location"]["lng"]
            station["distance"] = haversine(home, (station_lat, station_lon))

        self._stations.sort(key=lambda x: x["distance"])

        # Create a dropdown list of stations, selected by ID and shown by name
        station_options = {
            station["stationId"]: station["stationName"] for station in self._stations
        }

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): vol.In(station_options),
                }
            ),
        )

    async def _async_fetch_stations(self) -> dict[str, str]:
        """Fetch stations from the Citibike GraphQL API asynchronously."""
        network = NetworkNames(self._config.get("network"))
        network_name = network.name

        # Check station cache
        if cached_data := StationCache.get_cached_data(network_name):
            self._stations = cached_data
            return {}

        _LOGGER.debug("[API] Fetching station list for network %s", network_name)

        region_codes = NetworkRegion[network_name].value
        all_stations: list[dict] = []

        for region_code in region_codes:
            query = {
                "query": GET_INIT_STATION_QUERY,
                "variables": {"input": {"regionCode": region_code}},
            }

            data = await fetch_graphql_data(
                NetworkGraphQLEndpoints[network_name], query
            )

            # Don't offer (or cache) a list that is missing a region
            if data.get("base") == "cannot_connect":
                _LOGGER.warning(
                    "[API] Connection failed for network %s region %s",
                    network_name,
                    region_code,
                )
                return {"base": "cannot_connect"}

            try:
                stations = data["data"]["supply"]["stations"]
            except (KeyError, TypeError):
                _LOGGER.warning(
                    "[API] Unexpected response for network %s region %s",
                    network_name,
                    region_code,
                )
                return {"base": "cannot_connect"}

            all_stations.extend(stations)

        if not all_stations:
            _LOGGER.warning("[API] No stations retrieved for network %s", network_name)
            return {"base": "cannot_connect"}

        self._stations = all_stations
        StationCache.update_cache(network_name, self._stations)

        _LOGGER.debug(
            "[Config] Found %d stations for network %s",
            len(self._stations),
            network_name,
        )

        return {}
