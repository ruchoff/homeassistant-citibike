"""Cache management for Citibike integration."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import ClassVar

_LOGGER = logging.getLogger(__name__)


@dataclass
class CacheData:
    """Class to hold cache data."""

    timestamp: datetime
    data: list[dict[str, any]]


class StationCache:
    """Cache manager for station configuration data."""

    _cache: ClassVar[dict[str, CacheData]] = {}
    TIMEOUT: ClassVar[timedelta] = timedelta(hours=6)

    @classmethod
    def get_cached_data(cls, network_name: str) -> list[dict[str, any]] | None:
        """Get cached station data if valid."""
        if (
            network_name in cls._cache
            and datetime.now() - cls._cache[network_name].timestamp < cls.TIMEOUT
        ):
            _LOGGER.debug(
                "[Station Cache] HIT - Network: %s - Stations: %d",
                network_name,
                len(cls._cache[network_name].data),
            )
            return cls._cache[network_name].data

        _LOGGER.debug("[Station Cache] MISS - Network: %s", network_name)
        return None

    @classmethod
    def update_cache(cls, network_name: str, data: list[dict[str, any]]) -> None:
        """Update station cache with new data."""
        cls._cache[network_name] = CacheData(
            timestamp=datetime.now(),
            data=data,
        )
        _LOGGER.debug(
            "[Station Cache] UPDATE - Network: %s - Stations: %d",
            network_name,
            len(data),
        )


class SensorDataCache:
    """Cache manager for sensor update data."""

    _cache: ClassVar[dict[str, CacheData]] = {}
    TIMEOUT: ClassVar[timedelta] = timedelta(minutes=5)

    @classmethod
    def get_cached_data(cls, network_name: str) -> list[dict[str, any]] | None:
        """Get cached sensor data if valid."""
        if (
            network_name in cls._cache
            and datetime.now() - cls._cache[network_name].timestamp < cls.TIMEOUT
        ):
            _LOGGER.debug(
                "[Sensor Cache] HIT - Network: %s - Stations: %d",
                network_name,
                len(cls._cache[network_name].data),
            )
            return cls._cache[network_name].data

        _LOGGER.debug("[Sensor Cache] MISS - Network: %s", network_name)
        return None

    @classmethod
    def update_cache(cls, network_name: str, data: list[dict[str, any]]) -> None:
        """Update sensor cache with new data."""
        cls._cache[network_name] = CacheData(
            timestamp=datetime.now(),
            data=data,
        )
        _LOGGER.debug(
            "[Sensor Cache] UPDATE - Network: %s - Stations: %d",
            network_name,
            len(data),
        )
