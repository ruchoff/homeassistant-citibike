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
    CONF_STATIONS,
    CONF_STATIONID,
    CONF_STATIONNAME,
    STATION_INFO_URL,
    STATION_STATUS_URL,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)
STATION_SCHEMA = vol.Schema(
    {vol.Required(CONF_STATIONID): cv.string, vol.Optional(CONF_STATIONNAME): cv.string}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STATIONS): vol.All(cv.ensure_list, [STATION_SCHEMA]),
    }
)


def setup_platform(
    hass: core.HomeAssistant,
    config: config_entries.ConfigEntry,
    add_devices,
    discovery_info=None,
):
    """Set up the Citibike sensors."""
    data = GBFSServiceData()
    data.update()
    sensors = [CitibikeSensor(station, data) for station in config.get(CONF_STATIONS)]
    add_devices(sensors, True)


class CitibikeSensor(Entity):
    """Sensor that reads the status for an Citibike station."""

    def __init__(self, inStation, data):
        """Initalize the sensor."""
        self._id = inStation["id"]
        self._internal_id = None
        self._data = data
        self._state = 0
        if "name" in inStation:
            self._name = inStation["name"]
        else:
            self._name = None

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
        self._num_bikes_disabled = 0

    @property
    def name(self):
        """Returns the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Returns the state of the sensor."""
        return self._num_bikes_available

    @property
    def unique_id(self):
        """Returns the state of the sensor."""
        return self._name

    @property
    def device_class(self):
        return None

    @property
    def unit_of_measurement(self):
        return "bikes"

    @property
    def icon(self):
        """Returns the icon used for the frontend."""
        return "mdi:bicycle"

    @property
    def extra_state_attributes(self):
        """Returns the attributes of the sensor."""
        attrs = {}

        attrs["station_id"] = self._id
        attrs["latitude"] = self._latitude
        attrs["longitude"] = self._longitude
        attrs["station_capacity"] = self._capacity
        attrs["last_reported"] = self._last_reported
        attrs["docks_available"] = self._docks_available
        attrs["is_renting"] = self._is_renting
        attrs["is_returning"] = self._is_returning
        attrs["num_bikes_available"] = self._num_bikes_available
        attrs["available_bike_types"] = {
            "Human Powered": self._num_bikes_available - self._num_ebikes_available,
            "Electric Powered": self._num_ebikes_available,
        }
        attrs["num_bikes_disabled"] = self._num_bikes_disabled
        attrs["num_docks_disabled"] = self._num_docks_disabled
        attrs["num_bikes_disabled"] = self._num_bikes_disabled

        return attrs

    def update(self):
        """Updates the sensor."""
        self._data.update()
        for station in self._data.station_info_data["data"]["stations"]:
            if station["short_name"] == self._id:
                if self._name is None:
                    self._name = "citibike_station_" + self._id + "_" + station["name"]
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


class GBFSServiceData(object):
    """Query GBFS API."""

    def __init__(self):
        self.station_info_data = None
        self.station_status_data = None

    def update(self):
        """Update data based on SCAN_INTERVAL."""
        station_info_response = requests.get(STATION_INFO_URL)
        if station_info_response.status_code != 200:
            _LOGGER.warning("Invalid response from station info API")
        else:
            self.station_info_data = station_info_response.json()

        station_status_response = requests.get(STATION_STATUS_URL)
        if station_status_response.status_code != 200:
            _LOGGER.warning("Invalid response from station info API")
        else:
            self.station_status_data = station_status_response.json()
