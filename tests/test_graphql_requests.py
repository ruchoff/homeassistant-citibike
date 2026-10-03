"""Tests for the Citibike GraphQL requests."""

from unittest.mock import patch

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

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


@pytest.fixture(autouse=True)
def no_retry_delay():
    """Do not wait between attempts."""
    with patch("custom_components.citibike.graphql_requests.RETRY_DELAY", 0):
        yield


@pytest.mark.parametrize(
    ("response", "attempts"),
    [
        ({"status": 504}, 3),
        ({"exc": ClientError()}, 3),
        ({"exc": TimeoutError()}, 3),
        ({"status": 400}, 1),
        ({"text": "not json"}, 1),
        ({"json": {"errors": [{"message": "nope"}], "data": None}}, 1),
        ({"json": {"data": {"supply": None}}}, 1),
    ],
)
async def test_fetch_stations_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    response: dict,
    attempts: int,
) -> None:
    """Failures raise one error type; only transient ones are retried."""
    aioclient_mock.post(ENDPOINT, **response)

    with pytest.raises(GraphQLRequestError):
        await fetch_stations(async_get_clientsession(hass), ENDPOINT, {})

    assert aioclient_mock.call_count == attempts


async def test_fetch_stations_retries(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A gateway timeout followed by a good response succeeds."""
    station = make_station("E 40 St & Park Ave", "motivate_BKN_1", 0, 0)
    responses = [
        AiohttpClientMockResponse("post", ENDPOINT, status=504),
        AiohttpClientMockResponse("post", ENDPOINT, json=supply_response([station])),
    ]

    async def respond(method, url, data):
        return responses.pop(0)

    aioclient_mock.post(ENDPOINT, side_effect=respond)

    stations = await fetch_stations(async_get_clientsession(hass), ENDPOINT, {})

    assert len(stations) == 1
    assert aioclient_mock.call_count == 2
