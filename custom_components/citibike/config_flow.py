"""Config flow for Citibike integration."""

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util.location import distance
import voluptuous as vol

from .const import (
    CONF_NETWORK,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    NETWORKS,
    NETWORKS_BY_KEY,
)
from .graphql_queries.get_init_station_query import GET_INIT_STATION_QUERY
from .graphql_requests import GraphQLRequestError, fetch_stations

_LOGGER = logging.getLogger(__name__)


class CitibikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Citibike."""

    VERSION = 1
    MINOR_VERSION = 3

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config: dict[str, Any] = {}
        self._stations: list[dict[str, Any]] = []
        self._station_choices: dict[str, dict[str, Any]] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step to select a network."""
        _LOGGER.debug("Starting user step to select a network")
        errors: dict[str, str] = {}

        if user_input is not None:
            self._config[CONF_NETWORK] = user_input[CONF_NETWORK]
            _LOGGER.debug("Network selected: %s", user_input[CONF_NETWORK])

            errors = await self._async_fetch_stations()
            if not errors:
                return await self.async_step_select_station()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORK): vol.In(
                        {network.key: network.name for network in NETWORKS}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_select_station(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the step to select a station within the selected network."""
        _LOGGER.debug("Starting step to select a station")
        errors: dict[str, str] = {}

        if user_input is not None and (
            station := self._find_station(user_input[CONF_STATION_ID])
        ):
            station_id = station["stationId"]
            station_name = station["stationName"]
            self._config[CONF_STATION_ID] = station_id
            self._config[CONF_STATION_NAME] = station_name
            _LOGGER.debug("Station selected: %s (%s)", station_name, station_id)

            network = NETWORKS_BY_KEY[self._config[CONF_NETWORK]]
            await self.async_set_unique_id(f"{network.key}_{station_id}")
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                "Creating entry for network %s and station %s",
                network.name,
                station_name,
            )
            return self.async_create_entry(
                title=f"{network.name} {station_name}",
                data=self._config,
            )

        if user_input is not None:
            errors[CONF_STATION_ID] = "invalid_station"

        # Sort stations by distance to home
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        self._stations.sort(
            key=lambda station: distance(
                home_lat,
                home_lon,
                station["location"]["lat"],
                station["location"]["lng"],
            )
        )

        # Create a dropdown of station names in order of distance. The frontend
        # only offers type-to-search on a dropdown that accepts custom values,
        # and then shows the option value in the box, so the names themselves
        # are the values and are mapped back to stations in _find_station.
        self._station_choices = {}
        for station in self._stations:
            label = name = station["stationName"]
            count = 1
            while label in self._station_choices:
                count += 1
                label = f"{name} ({count})"
            self._station_choices[label] = station

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=list(self._station_choices),
                            mode=SelectSelectorMode.DROPDOWN,
                            custom_value=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    def _find_station(self, value: str) -> dict[str, Any] | None:
        """Return the station picked from the list or typed by name."""
        if station := self._station_choices.get(value):
            return station

        # Typed text is only accepted when it names exactly one station
        name = value.strip().casefold()
        matches = [
            station
            for label, station in self._station_choices.items()
            if label.casefold() == name
        ]
        return matches[0] if len(matches) == 1 else None

    async def _async_fetch_stations(self) -> dict[str, str]:
        """Fetch stations from the Citibike GraphQL API asynchronously."""
        network = NETWORKS_BY_KEY[self._config[CONF_NETWORK]]
        network_name = network.name

        # A network that is already set up has an up to date station list
        coordinator = self.hass.data.get(DOMAIN, {}).get(network.key)
        if coordinator is not None and coordinator.last_update_success:
            self._stations = list(coordinator.data.values())
            return {}

        _LOGGER.debug("[API] Fetching station list for network %s", network_name)

        region_codes = network.regions
        session = async_get_clientsession(self.hass)
        all_stations: list[dict[str, Any]] = []

        for region_code in region_codes:
            query = {
                "query": GET_INIT_STATION_QUERY,
                "variables": {"input": {"regionCode": region_code}},
            }

            # Don't offer a list that is missing a region
            try:
                stations = await fetch_stations(session, network.endpoint, query)
            except GraphQLRequestError as err:
                _LOGGER.warning(
                    "[API] Fetch failed for network %s region %s: %s",
                    network_name,
                    region_code,
                    err,
                )
                return {"base": "cannot_connect"}

            all_stations.extend(stations)

        if not all_stations:
            _LOGGER.warning("[API] No stations retrieved for network %s", network_name)
            return {"base": "cannot_connect"}

        self._stations = all_stations

        _LOGGER.debug(
            "[Config] Found %d stations for network %s",
            len(self._stations),
            network_name,
        )

        return {}
