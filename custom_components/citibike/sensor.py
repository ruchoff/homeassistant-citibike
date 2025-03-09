"""
Sensor for checking the status of Citi Bike stations.
"""

import logging
from datetime import timedelta, datetime

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant import core, config_entries

from .const import (
    CONF_STATIONID,
    CONF_SENSORNAME,
    STATION_INFO_URL,
    STATION_STATUS_URL,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STATIONID): cv.string,
        vol.Optional(CONF_SENSORNAME): cv.string,
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up the Citibike sensors from a config entry."""
    data = GBFSServiceData()
    await hass.async_add_executor_job(data.update)
    sensor = CitibikeSensor(entry.data, data)
    async_add_entities([sensor], True)


def setup_platform(
    hass: core.HomeAssistant,
    config: config_entries.ConfigEntry,
    add_devices,
    discovery_info=None,
):
    """Set up the Citibike sensors."""
    data = GBFSServiceData()
    data.update()
    sensor = CitibikeSensor(config, data)
    add_devices([sensor], True)


class CitibikeSensor(Entity):
    """Sensor that reads the status for a Citibike station."""

    def __init__(self, config: dict, data: "GBFSServiceData"):
        """Initialize the sensor."""
        self._id = config[CONF_STATIONID]
        self._internal_id = None
        self._data = data
        self._state = 0

        # Fetch the station short_name if CONF_SENSORNAME is not provided
        station_name = config.get(CONF_SENSORNAME)
        if not station_name:
            for station in data.station_info_data["data"]["stations"]:
                if station["short_name"] == self._id:
                    station_name = f"citibike_station_{self._id}_{station['name']}"
                    break
        self._name = station_name or f"citibike_station_{self._id}"

        self._latitude = None
        self._longitude = None
        self._capacity = 0
        self._region = None

        self._last_reported = None
        self._docks_available = 0
        self._is_renting = False
        self._is_returning = False
        self._num_bikes_available = 0
        self._num_ebikes_available = 0
        self._num_bikes_disabled = 0
        self._num_docks_disabled = 0

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._num_bikes_available

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
        return "bikes"

    @property
    def icon(self) -> str:
        """Return the icon used for the frontend."""
        return "mdi:bicycle"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the attributes of the sensor."""
        return {
            "station_id": self._id,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "station_capacity": self._capacity,
            "last_reported": self._last_reported,
            "docks_available": self._docks_available,
            "is_renting": self._is_renting,
            "is_returning": self._is_returning,
            "num_bikes_available": self._num_bikes_available,
            "available_bike_types": {
                "Human Powered": self._num_bikes_available - self._num_ebikes_available,
                "Electric Powered": self._num_ebikes_available,
            },
            "num_bikes_disabled": self._num_bikes_disabled,
            "num_docks_disabled": self._num_docks_disabled,
        }

    def update(self) -> None:
        """Update the sensor."""
        self._data.update()
        for station in self._data.station_info_data["data"]["stations"]:
            if station["short_name"] == self._id:
                self._latitude = station["lat"]
                self._longitude = station["lon"]
                self._capacity = station["capacity"]
                self._region = station["region_id"]
                self._internal_id = station["station_id"]

        for station in self._data.station_status_data["data"]["stations"]:
            if station["station_id"] == self._internal_id:
                self._last_reported = datetime.fromtimestamp(station["last_reported"])
                self._docks_available = station["num_docks_available"]
                self._is_renting = bool(station["is_renting"])
                self._is_returning = bool(station["is_returning"])
                self._num_bikes_available = station["num_bikes_available"]
                self._num_ebikes_available = station["num_ebikes_available"]
                self._num_bikes_disabled = station["num_bikes_disabled"]
                self._num_docks_disabled = station["num_docks_disabled"]

                self._state = station["num_bikes_available"]


class GBFSServiceData:
    """Query GBFS API."""

    def __init__(self) -> None:
        self.station_info_data = None
        self.station_status_data = None

    def update(self) -> None:
        """Update data based on SCAN_INTERVAL."""
        station_info_response = requests.get(STATION_INFO_URL)
        if station_info_response.status_code != 200:
            _LOGGER.warning("Invalid response from station info API")
        else:
            self.station_info_data = station_info_response.json()

        station_status_response = requests.get(STATION_STATUS_URL)
        if station_status_response.status_code != 200:
            _LOGGER.warning("Invalid response from station status API")
        else:
            self.station_status_data = station_status_response.json()
