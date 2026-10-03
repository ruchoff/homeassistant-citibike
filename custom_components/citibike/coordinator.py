"""Data update coordinator for the Citibike integration."""

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL, Network
from .graphql_queries.get_supply_query import GET_SUPPLY_QUERY
from .graphql_requests import GraphQLRequestError, fetch_stations

_LOGGER = logging.getLogger(__name__)


class CitibikeCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch all stations of one network, shared by every sensor on it."""

    def __init__(self, hass: HomeAssistant, network: Network) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=None,
            name=f"{DOMAIN}_{network.key}",
            update_interval=UPDATE_INTERVAL,
        )
        self.network = network
        self._load_lock = asyncio.Lock()

    async def async_ensure_loaded(self) -> None:
        """Fetch initial data unless another config entry already did."""
        async with self._load_lock:
            if self.data is None:
                await self.async_refresh()

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch the stations of every region, keyed by station ID."""
        network = self.network
        session = async_get_clientsession(self.hass)
        stations: dict[str, dict[str, Any]] = {}

        for region_code in network.regions:
            query = {
                "query": GET_SUPPLY_QUERY,
                "variables": {
                    "input": {"regionCode": region_code, "rideablePageLimit": 1000}
                },
            }

            # A partial result would make the missing region's stations look
            # removed, so fail the whole update instead.
            try:
                region_stations = await fetch_stations(session, network.endpoint, query)
            except GraphQLRequestError as err:
                raise UpdateFailed(
                    f"Fetch failed for network {network.name} region {region_code}: {err}"
                ) from err

            for station in region_stations:
                stations[station["stationId"]] = station

        if not stations:
            raise UpdateFailed(f"No stations retrieved for network {network.name}")

        return stations
