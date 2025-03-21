import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Default headers
DEFAULT_HEADERS = {"Content-Type": "application/json"}


async def fetch_graphql_data(
    endpoint: str, query: dict[str, Any], headers: dict[str, str] | None = None
) -> dict[str, Any]:
    """Fetch data from the GraphQL API and clean it."""
    # Use default headers if no headers are passed
    if headers is None:
        headers = DEFAULT_HEADERS

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=query, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to connect: %s, %s",
                        response.status,
                        await response.text(),
                    )
                    return {"base": "cannot_connect"}

                data = await response.json()
                _LOGGER.debug("Response data: %s", json.dumps(data, indent=2))

                # Clean the data here
                clean_data(data)

                return data
    except Exception as e:
        _LOGGER.error("Error during GraphQL request: %s", str(e))
        return {"base": "cannot_connect"}


def clean_data(data: dict[str, Any]) -> None:
    """Clean the rideable names by replacing Unicode characters."""
    if "data" in data and "supply" in data["data"]:
        for station in data["data"]["supply"].get("stations", []):
            for ebike in station.get("ebikes", []):
                if "rideableName" in ebike:
                    ebike["rideableName"] = ebike["rideableName"].replace("\u00b7", ".")

            for scooter in station.get("scooters", []):
                if "rideableName" in scooter:
                    scooter["rideableName"] = scooter["rideableName"].replace(
                        "\u00b7", "."
                    )
    else:
        _LOGGER.warning("Data format is unexpected, cannot clean the rideable names")
