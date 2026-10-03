"""Data update coordinator for the Citibike integration."""

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    NetworkGraphQLEndpoints,
    NetworkNames,
    NetworkRegion,
)
from .graphql_queries.get_supply_query import GET_SUPPLY_QUERY
from .graphql_requests import fetch_graphql_data

_LOGGER = logging.getLogger(__name__)


class CitibikeCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch all stations of one network, shared by every sensor on it."""

    def __init__(self, hass: HomeAssistant, network: NetworkNames) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=None,
            name=f"{DOMAIN}_{network.name.lower()}",
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
        """Fetch the stations of every region, keyed by station name."""
        network_name = self.network.name
        stations: dict[str, dict[str, Any]] = {}

        for region_code in NetworkRegion[network_name].value:
            query = {
                "query": GET_SUPPLY_QUERY,
                "variables": {
                    "input": {"regionCode": region_code, "rideablePageLimit": 1000}
                },
            }

            data = await fetch_graphql_data(
                NetworkGraphQLEndpoints[network_name], query
            )

            # A partial result would make the missing region's stations look
            # removed, so fail the whole update instead.
            if data.get("base") == "cannot_connect":
                raise UpdateFailed(
                    f"Connection failed for network {network_name} region {region_code}"
                )

            try:
                region_stations = data["data"]["supply"]["stations"]
            except (KeyError, TypeError) as err:
                raise UpdateFailed(
                    f"Unexpected response for network {network_name} region {region_code}"
                ) from err

            for station in region_stations:
                stations[station["stationName"]] = station

        if not stations:
            raise UpdateFailed(f"No stations retrieved for network {network_name}")

        return stations
