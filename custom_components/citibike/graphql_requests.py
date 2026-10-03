"""GraphQL requests for the Citibike integration."""

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

# The API is slow and regularly answers 504 when its own backend times out
MAX_ATTEMPTS = 3
RETRY_DELAY = 2


class GraphQLRequestError(Exception):
    """The GraphQL API could not be reached or returned an unusable response."""


class _TransientRequestError(GraphQLRequestError):
    """A failure that is worth retrying."""


async def fetch_stations(
    session: aiohttp.ClientSession,
    endpoint: str,
    query: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fetch the stations of a supply query from the GraphQL API and clean them."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            data = await _post(session, endpoint, query)
            break
        except _TransientRequestError as err:
            if attempt == MAX_ATTEMPTS:
                raise
            _LOGGER.debug(
                "Attempt %d of %d failed, retrying: %s", attempt, MAX_ATTEMPTS, err
            )
            await asyncio.sleep(RETRY_DELAY)

    try:
        stations = data["data"]["supply"]["stations"]
    except (KeyError, TypeError) as err:
        raise GraphQLRequestError(f"Unexpected response from {endpoint}") from err

    _LOGGER.debug("Successfully fetched data from GraphQL API")
    clean_data(stations)

    return stations


async def _post(
    session: aiohttp.ClientSession, endpoint: str, query: dict[str, Any]
) -> Any:
    """Post a query and return the decoded JSON response."""
    try:
        async with session.post(
            endpoint, json=query, timeout=REQUEST_TIMEOUT
        ) as response:
            if response.status >= 500:
                raise _TransientRequestError(
                    f"{endpoint} returned HTTP {response.status}"
                )
            if response.status != 200:
                raise GraphQLRequestError(f"{endpoint} returned HTTP {response.status}")
            return await response.json()
    except (aiohttp.ContentTypeError, ValueError) as err:
        raise GraphQLRequestError(f"Invalid response from {endpoint}: {err!r}") from err
    except (aiohttp.ClientError, TimeoutError) as err:
        raise _TransientRequestError(f"Error requesting {endpoint}: {err!r}") from err


def clean_data(stations: list[dict[str, Any]]) -> None:
    """Clean the rideable names by replacing Unicode characters."""
    for station in stations:
        for rideable in (station.get("ebikes") or []) + (station.get("scooters") or []):
            if rideable and rideable.get("rideableName"):
                rideable["rideableName"] = rideable["rideableName"].replace("·", ".")
