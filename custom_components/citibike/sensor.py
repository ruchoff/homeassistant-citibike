"""Integration for Citibike sensors."""

from datetime import datetime
import logging
from typing import Any

from homeassistant import config_entries, core
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, CONF_STATION_NAME
from .coordinator import CitibikeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
) -> None:
    """Set up the Citibike sensors from a config entry."""
    _LOGGER.debug("Setting up Citibike sensor entry")
    async_add_entities([CitibikeSensor(entry.runtime_data, entry.data)])


class CitibikeSensor(CoordinatorEntity[CitibikeCoordinator]):
    """Sensor that reads the status for a Citibike station."""

    def __init__(self, coordinator: CitibikeCoordinator, config: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._id = config[CONF_STATION_ID]
        self._network = coordinator.network.value
        self._name = f"{self._network}_{config[CONF_STATION_NAME]}"
        self._unique_id = f"{coordinator.network.name.lower()}_{self._id}"

    @property
    def _station(self) -> dict[str, Any] | None:
        """Return the latest data for this station, if the network reports it."""
        return self.coordinator.data.get(self._id)

    @property
    def available(self) -> bool:
        """Return if the last update succeeded and included this station."""
        return super().available and self._station is not None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        if (station := self._station) is None:
            return None
        return station["totalRideablesAvailable"]

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return None

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of the sensor."""
        return "rideables"

    @property
    def icon(self) -> str:
        """Return the icon used for the frontend."""
        return "mdi:bicycle"

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the attributes of the sensor."""
        if (station := self._station) is None:
            return None

        ebike_status = [
            {
                "bike_id": ebike["rideableName"],
                "battery_percent": ebike["batteryStatus"]["percent"],
                "distance_remaining": ebike["batteryStatus"]["distanceRemaining"][
                    "value"
                ],
                "distance_remaining_units": ebike["batteryStatus"]["distanceRemaining"][
                    "unit"
                ],
            }
            for ebike in station["ebikes"]
        ]

        return {
            "station_id": station["siteId"],
            "station_name": station["stationName"],
            "network": self._network,
            "latitude": station["location"]["lat"],
            "longitude": station["location"]["lng"],
            "total_rideables_available": station["totalRideablesAvailable"],
            "station_capacity": station["totalBikesAvailable"]
            + station["bikeDocksAvailable"],
            "docks_available": station["bikeDocksAvailable"],
            "available_bike_types": {
                "Human Powered": station["bikesAvailable"],
                "Electric Powered": station["ebikesAvailable"],
            },
            "max_ebike_distance": max(
                (ebike["distance_remaining"] for ebike in ebike_status),
                default=0,
            ),
            "ebike_status": ebike_status,
            "last_reported": datetime.fromtimestamp(station["lastUpdatedMs"] / 1000),
            "is_offline": station["isOffline"],
        }
