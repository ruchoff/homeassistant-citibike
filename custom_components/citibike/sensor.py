"""Integration for Citibike sensors."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN
from .coordinator import CitibikeConfigEntry, CitibikeCoordinator

_LOGGER = logging.getLogger(__name__)


def _ebike_status(station: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the status of the station's e-bikes.

    The API can leave out a bike's battery or range, which is reported as None
    rather than failing the whole station.
    """
    status = []
    for ebike in station.get("ebikes") or []:
        if not ebike:
            continue
        battery = ebike.get("batteryStatus") or {}
        distance = battery.get("distanceRemaining") or {}
        status.append(
            {
                "bike_id": ebike.get("rideableName"),
                "battery_percent": battery.get("percent"),
                "distance_remaining": distance.get("value"),
                "distance_remaining_units": distance.get("unit"),
            }
        )
    return status


def _max_ebike_distance(station: dict[str, Any]) -> float:
    """Return the longest remaining range of the station's e-bikes."""
    return max(
        (
            ebike["distance_remaining"]
            for ebike in _ebike_status(station)
            if ebike["distance_remaining"] is not None
        ),
        default=0,
    )


@dataclass(frozen=True, kw_only=True)
class CitibikeSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor for one value of a station."""

    value_fn: Callable[[dict[str, Any]], int | float]


SENSOR_DESCRIPTIONS: tuple[CitibikeSensorEntityDescription, ...] = (
    CitibikeSensorEntityDescription(
        key="docks_available",
        translation_key="docks_available",
        native_unit_of_measurement="docks",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station["bikeDocksAvailable"],
    ),
    CitibikeSensorEntityDescription(
        key="bikes_available",
        translation_key="bikes_available",
        native_unit_of_measurement="bikes",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station["bikesAvailable"],
    ),
    CitibikeSensorEntityDescription(
        key="ebikes_available",
        translation_key="ebikes_available",
        native_unit_of_measurement="bikes",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station["ebikesAvailable"],
    ),
    CitibikeSensorEntityDescription(
        key="max_ebike_distance",
        translation_key="max_ebike_distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_max_ebike_distance,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CitibikeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Citibike sensors from a config entry."""
    _LOGGER.debug("Setting up Citibike sensor entry")
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CitibikeSensor(coordinator, entry.data),
            *(
                CitibikeStationValueSensor(coordinator, entry.data, description)
                for description in SENSOR_DESCRIPTIONS
            ),
        ]
    )


class CitibikeStationEntity(CoordinatorEntity[CitibikeCoordinator], SensorEntity):
    """Base for sensors that read the status of a Citibike station."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CitibikeCoordinator, config: Mapping[str, Any]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._id = config[CONF_STATION_ID]
        self._network = coordinator.network.name
        self._station_unique_id = f"{coordinator.network.key}_{self._id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._station_unique_id)},
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


class CitibikeSensor(CitibikeStationEntity):
    """Sensor for the rideables available at a Citibike station."""

    # The sensor is the station's main feature, so it takes the device name
    _attr_name = None
    _attr_translation_key = "rideables"
    _attr_native_unit_of_measurement = "rideables"
    _attr_state_class = SensorStateClass.MEASUREMENT
    # A per-bike list that changes on almost every update
    _unrecorded_attributes = frozenset({"ebike_status"})

    def __init__(
        self, coordinator: CitibikeCoordinator, config: Mapping[str, Any]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config)
        self._attr_unique_id = self._station_unique_id

    @property
    def native_value(self) -> int | None:
        """Return the number of rideables available at the station."""
        if (station := self._station) is None:
            return None
        return station["totalRideablesAvailable"]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the attributes of the sensor."""
        if (station := self._station) is None:
            return None

        ebike_status = _ebike_status(station)

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
                (
                    ebike["distance_remaining"]
                    for ebike in ebike_status
                    if ebike["distance_remaining"] is not None
                ),
                default=0,
            ),
            "ebike_status": ebike_status,
            "last_reported": dt_util.utc_from_timestamp(
                station["lastUpdatedMs"] / 1000
            ),
            "is_offline": station["isOffline"],
        }


class CitibikeStationValueSensor(CitibikeStationEntity):
    """Sensor for a single value of a Citibike station."""

    entity_description: CitibikeSensorEntityDescription

    def __init__(
        self,
        coordinator: CitibikeCoordinator,
        config: Mapping[str, Any],
        description: CitibikeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config)
        self.entity_description = description
        self._attr_unique_id = f"{self._station_unique_id}_{description.key}"

    @property
    def native_value(self) -> int | float | None:
        """Return the value of the sensor."""
        if (station := self._station) is None:
            return None
        return self.entity_description.value_fn(station)
