"""Integration for Citi Bike."""

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_LEGACY_STATION_NAME,
    CONF_NETWORK,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    NETWORKS_BY_NAME,
)
from .coordinator import CitibikeCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Citibike integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Citibike from a config entry."""
    network = NETWORKS_BY_NAME[entry.data[CONF_NETWORK]]

    # One coordinator per network, shared by all of its stations
    coordinators = hass.data.setdefault(DOMAIN, {})
    if (coordinator := coordinators.get(network.key)) is None:
        coordinator = coordinators[network.key] = CitibikeCoordinator(hass, network)

    await coordinator.async_ensure_loaded()
    if coordinator.data is None:
        raise ConfigEntryNotReady(f"Could not fetch stations for {network.name}")

    if CONF_STATION_ID not in entry.data:
        _async_migrate_station_name(hass, entry, coordinator)

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _async_migrate_station_name(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: CitibikeCoordinator
) -> None:
    """Identify a station that was configured by name by its station ID."""
    station_name = entry.data[CONF_LEGACY_STATION_NAME]
    station = next(
        (s for s in coordinator.data.values() if s["stationName"] == station_name),
        None,
    )
    if station is None:
        raise ConfigEntryError(
            f"Station {station_name} no longer exists on {coordinator.network.name}; "
            "remove it and add the station again"
        )

    station_id = station["stationId"]
    unique_id = f"{coordinator.network.key}_{station_id}"

    # The entity used the station name as its unique ID; keep its history
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id == station_name:
            registry.async_update_entity(entity.entity_id, new_unique_id=unique_id)

    hass.config_entries.async_update_entry(
        entry,
        data={
            CONF_NETWORK: entry.data[CONF_NETWORK],
            CONF_STATION_ID: station_id,
            CONF_STATION_NAME: station_name,
        },
        unique_id=unique_id,
        minor_version=2,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Drop the coordinator once no other loaded entry uses its network
        network = entry.runtime_data.network
        if not any(
            other.entry_id != entry.entry_id
            and other.state is ConfigEntryState.LOADED
            and other.data[CONF_NETWORK] == network.name
            for other in hass.config_entries.async_entries(DOMAIN)
        ):
            hass.data[DOMAIN].pop(network.key, None)

    return unload_ok
