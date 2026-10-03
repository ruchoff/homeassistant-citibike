"""Integration for Citi Bike."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    CONF_LEGACY_STATION_NAME,
    CONF_NETWORK,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    LEGACY_NETWORK_KEYS,
    NETWORKS_BY_KEY,
    Network,
)
from .coordinator import CitibikeConfigEntry, CitibikeCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: CitibikeConfigEntry) -> bool:
    """Set up Citibike from a config entry."""
    network = _async_get_network(hass, entry)

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

    @callback
    def _async_sync_station_name() -> None:
        """Follow a station or network that was renamed."""
        _async_update_station_name(hass, entry, coordinator)

    _async_sync_station_name()
    entry.async_on_unload(coordinator.async_add_listener(_async_sync_station_name))
    return True


def _async_update_station_name(
    hass: HomeAssistant, entry: CitibikeConfigEntry, coordinator: CitibikeCoordinator
) -> None:
    """Keep the entry and its device named after the network and station."""
    network = coordinator.network
    station = coordinator.data.get(entry.data[CONF_STATION_ID])
    old_name = entry.data[CONF_STATION_NAME]
    new_name = station["stationName"] if station else old_name

    # Leave a title the user has changed alone
    title = entry.title
    if title in {
        f"{network_name} {old_name}"
        for network_name in (network.name, *network.former_names)
    }:
        title = f"{network.name} {new_name}"

    if new_name == old_name and title == entry.title:
        return

    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_STATION_NAME: new_name}, title=title
    )

    if new_name == old_name:
        return

    # A name the user gave the device is stored separately and is kept
    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        device_registry.async_update_device(
            device.id, name=f"{network.name} {new_name}"
        )


def _async_get_network(hass: HomeAssistant, entry: CitibikeConfigEntry) -> Network:
    """Return the entry's network, migrating a network stored by display name."""
    value = entry.data[CONF_NETWORK]
    if (network := NETWORKS_BY_KEY.get(value)) is not None:
        return network

    if (key := LEGACY_NETWORK_KEYS.get(value)) is None:
        raise ConfigEntryError(
            f"The {value} network is no longer supported; remove this station"
        )

    # An entry that also lacks a station ID gets its version from that migration
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, CONF_NETWORK: key},
        minor_version=3 if CONF_STATION_ID in entry.data else entry.minor_version,
    )
    return NETWORKS_BY_KEY[key]


def _async_migrate_station_name(
    hass: HomeAssistant, entry: CitibikeConfigEntry, coordinator: CitibikeCoordinator
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
        minor_version=3,
    )


async def async_unload_entry(hass: HomeAssistant, entry: CitibikeConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Drop the coordinator once no other loaded entry uses its network
        network = entry.runtime_data.network
        if not any(
            other.entry_id != entry.entry_id
            and other.state is ConfigEntryState.LOADED
            and other.data[CONF_NETWORK] == network.key
            for other in hass.config_entries.async_entries(DOMAIN)
        ):
            hass.data[DOMAIN].pop(network.key, None)

    return unload_ok
