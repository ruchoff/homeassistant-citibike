"""Tests for the Citibike GraphQL requests."""

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.citibike.const import NETWORKS_BY_KEY
from custom_components.citibike.graphql_requests import (
    GraphQLRequestError,
    fetch_stations,
)

from .conftest import make_station, supply_response

ENDPOINT = NETWORKS_BY_KEY["citibike"].endpoint


async def test_fetch_stations(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Stations are returned with cleaned rideable names."""
    station = make_station("E 40 St & Park Ave", "motivate_BKN_1", 0, 0)
    station["ebikes"][0]["rideableName"] = "123\u00b74567"
    station["ebikes"][1]["rideableName"] = None
    station["ebikes"].append(None)
    station["scooters"] = None
    aioclient_mock.post(ENDPOINT, json=supply_response([station]))

    stations = await fetch_stations(async_get_clientsession(hass), ENDPOINT, {})

    assert stations[0]["stationName"] == "E 40 St & Park Ave"
    assert stations[0]["ebikes"][0]["rideableName"] == "123.4567"


@pytest.mark.parametrize(
    "response",
    [
        {"status": 504},
        {"exc": ClientError()},
        {"exc": TimeoutError()},
        {"text": "not json"},
        {"json": {"errors": [{"message": "nope"}], "data": None}},
        {"json": {"data": {"supply": None}}},
    ],
)
async def test_fetch_stations_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, response: dict
) -> None:
    """Connection problems and unusable responses raise one error type."""
    aioclient_mock.post(ENDPOINT, **response)

    with pytest.raises(GraphQLRequestError):
        await fetch_stations(async_get_clientsession(hass), ENDPOINT, {})
