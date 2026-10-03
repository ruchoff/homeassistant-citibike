"""Integration for Citibike sensors."""

import logging
from typing import Any

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN
from .coordinator import CitibikeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
) -> None:
    """Set up the Citibike sensors from a config entry."""
    _LOGGER.debug("Setting up Citibike sensor entry")
    async_add_entities([CitibikeSensor(entry.runtime_data, entry.data)])


class CitibikeSensor(CoordinatorEntity[CitibikeCoordinator], SensorEntity):
    """Sensor that reads the status for a Citibike station."""

    # The sensor is the station's main feature, so it takes the device name
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:bicycle"
    _attr_native_unit_of_measurement = "rideables"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: CitibikeCoordinator, config: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._id = config[CONF_STATION_ID]
        self._network = coordinator.network.value
        self._attr_unique_id = f"{coordinator.network.name.lower()}_{self._id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=f"{self._network} {config[CONF_STATION_NAME]}",
            manufacturer=self._network,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _station(self) -> dict[str, Any] | None:
        """Return the latest data for this station, if the network reports it."""
        return self.coordinator.data.get(self._id)

    @property
    def available(self) -> bool:
        """Return if the last update succeeded and included this station."""
        return super().available and self._station is not None

    @property
    def native_value(self) -> int | None:
        """Return the number of rideables available at the station."""
        if (station := self._station) is None:
            return None
        return station["totalRideablesAvailable"]

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
            "last_reported": dt_util.utc_from_timestamp(
                station["lastUpdatedMs"] / 1000
            ),
            "is_offline": station["isOffline"],
        }
