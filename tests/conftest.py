"""Fixtures for the Citibike integration tests."""

from unittest.mock import patch

import pytest

from custom_components.citibike.cache import StationCache


def make_station(
    name: str, station_id: str, lat: float, lng: float, **overrides
) -> dict:
    """Build a station as returned by the supply query."""
    station = {
        "stationId": station_id,
        "stationName": name,
        "siteId": "6432.11",
        "location": {"lat": lat, "lng": lng},
        "totalBikesAvailable": 7,
        "bikeDocksAvailable": 10,
        "lastUpdatedMs": 1735772399000,
        "bikesAvailable": 5,
        "ebikesAvailable": 2,
        "isOffline": False,
        "totalRideablesAvailable": 7,
        "ebikes": [
            {
                "rideableName": "123-4567",
                "batteryStatus": {
                    "percent": 99,
                    "distanceRemaining": {"value": 35, "unit": "mi"},
                },
            },
            {
                "rideableName": "765-4321",
                "batteryStatus": {
                    "percent": 40,
                    "distanceRemaining": {"value": 12, "unit": "mi"},
                },
            },
        ],
    }
    station.update(overrides)
    return station


STATIONS = [
    make_station("E 40 St & Park Ave", "motivate_BKN_1", 40.7505, -73.9781),
    make_station("W 21 St & 6 Ave", "motivate_BKN_2", 40.7417, -73.9942),
]


def supply_response(stations: list[dict]) -> dict:
    """Wrap stations the way the GraphQL API does."""
    return {"data": {"supply": {"stations": stations}}}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading the integration under test."""
    return


@pytest.fixture(autouse=True)
def clear_station_cache():
    """Keep the config flow station cache from leaking between tests."""
    StationCache._cache.clear()
    yield
    StationCache._cache.clear()


@pytest.fixture
def mock_fetch():
    """Patch the GraphQL request used by the coordinator and config flow."""
    with (
        patch(
            "custom_components.citibike.coordinator.fetch_stations",
            return_value=STATIONS,
        ) as fetch,
        patch("custom_components.citibike.config_flow.fetch_stations", new=fetch),
    ):
        yield fetch
