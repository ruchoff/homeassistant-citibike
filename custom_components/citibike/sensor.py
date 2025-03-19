"""Integration for Citibike sensors."""

from datetime import datetime, timedelta
import logging

import voluptuous as vol

from config.custom_components.citibike.graphql_queries.get_supply_query import (
    GET_SUPPLY_QUERY,
)
from config.custom_components.citibike.graphql_requests import fetch_graphql_data
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import CONF_STATIONID

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)

SENSOR_PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STATIONID): cv.string,
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
) -> None:
    """Set up the Citibike sensors from a config entry."""
    data = GQLServiceData(entry.data)
    await data.update()
    sensor = CitibikeSensor(entry.data, data)
    async_add_entities([sensor], True)


def setup_platform(
    hass: core.HomeAssistant,
    config: config_entries.ConfigEntry,
    add_devices,
    discovery_info=None,
) -> None:
    """Set up the Citibike sensors."""
    data = GQLServiceData(config)
    data.update()
    sensor = CitibikeSensor(config, data)
    add_devices([sensor], True)


class CitibikeSensor(Entity):
    """Sensor that reads the status for a Citibike station."""

    def __init__(self, config: dict, data: "GQLServiceData") -> None:
        """Initialize the sensor."""
        self._id = config[CONF_STATIONID]
        self._data = data
        self._state = 0

        station = data.station_data
        station_name = f"citibike_station_{self._id}_{station['stationName']}"
        self._name = station_name
        self._station_name = station["stationName"]

        self._latitude = None
        self._longitude = None
        self._capacity = 0
        self._region = None

        self._last_reported = None
        self._docks_available = 0
        self._num_bikes_available = 0
        self._num_ebikes_available = 0
        self._is_offline = False
        self._total_rideables_available = 0
        self._ebike_status = []
        self._max_ebike_distance = 0

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._total_rideables_available

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._id

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
    def extra_state_attributes(self) -> dict:
        """Return the attributes of the sensor."""
        return {
            "station_id": self._id,
            "station_name": self._station_name,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "total_rideables_available": self._total_rideables_available,
            "station_capacity": self._capacity,
            "docks_available": self._docks_available,
            "available_bike_types": {
                "Human Powered": self._num_bikes_available,
                "Electric Powered": self._num_ebikes_available,
            },
            "max_ebike_distance": self._max_ebike_distance,
            "ebike_status": self._ebike_status,
            "last_reported": self._last_reported,
            "is_offline": self._is_offline,
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        await self._data.update()
        station = self._data.station_data
        self._latitude = station["location"]["lat"]
        self._longitude = station["location"]["lng"]
        self._capacity = station["totalBikesAvailable"] + station["bikeDocksAvailable"]
        self._last_reported = datetime.fromtimestamp(station["lastUpdatedMs"] / 1000)
        self._docks_available = station["bikeDocksAvailable"]
        self._num_bikes_available = station["bikesAvailable"]
        self._num_ebikes_available = station["ebikesAvailable"]
        self._is_offline = station["isOffline"]
        self._total_rideables_available = station["totalRideablesAvailable"]

        self._ebike_status = [
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
        self._max_ebike_distance = max(
            (
                ebike["batteryStatus"]["distanceRemaining"]["value"]
                for ebike in station["ebikes"]
            ),
            default=0,
        )

        self._state = station["totalRideablesAvailable"]


class GQLServiceData:
    """Query GQL API for Citibike data."""

    def __init__(self, config: dict) -> None:
        """Initialize the GBFSServiceData."""
        self._config = config
        self.station_data = None

    async def update(self) -> None:
        """Update data based on SCAN_INTERVAL."""
        data = await fetch_graphql_data(GET_SUPPLY_QUERY)

        if data.get("base") == "cannot_connect":
            _LOGGER.warning("Cannot connect to the GQL API")
            return

        # Get the station data by siteId
        station_id = self._config[CONF_STATIONID]
        self.station_data = next(
            (
                station
                for station in data["data"]["supply"]["stations"]
                if station["siteId"] == station_id
            ),
            None,
        )
