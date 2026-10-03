import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Default headers
DEFAULT_HEADERS = {"Content-Type": "application/json"}

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class GraphQLRequestError(Exception):
    """The GraphQL API could not be reached or returned an unusable response."""


async def fetch_stations(
    session: aiohttp.ClientSession,
    endpoint: str,
    query: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch the stations of a supply query from the GraphQL API and clean them."""
    # Use default headers if no headers are passed
    if headers is None:
        headers = DEFAULT_HEADERS

    try:
        async with session.post(
            endpoint, json=query, headers=headers, timeout=REQUEST_TIMEOUT
        ) as response:
            if response.status != 200:
                raise GraphQLRequestError(f"{endpoint} returned HTTP {response.status}")
            data = await response.json()
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise GraphQLRequestError(f"Error requesting {endpoint}: {err!r}") from err

    try:
        stations = data["data"]["supply"]["stations"]
    except (KeyError, TypeError) as err:
        raise GraphQLRequestError(f"Unexpected response from {endpoint}") from err

    _LOGGER.debug("Successfully fetched data from GraphQL API")
    clean_data(stations)

    return stations


def clean_data(stations: list[dict[str, Any]]) -> None:
    """Clean the rideable names by replacing Unicode characters."""
    for station in stations:
        for ebike in station.get("ebikes", []):
            if "rideableName" in ebike:
                ebike["rideableName"] = ebike["rideableName"].replace("·", ".")

        for scooter in station.get("scooters", []):
            if "rideableName" in scooter:
                scooter["rideableName"] = scooter["rideableName"].replace(
                    "·", "."
                )
