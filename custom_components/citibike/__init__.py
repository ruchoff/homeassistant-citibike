"""Integration for Citi Bike."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, NetworkNames
from .coordinator import CitibikeCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Citibike integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Citibike from a config entry."""
    network = NetworkNames(entry.data["network"])

    # One coordinator per network, shared by all of its stations
    coordinators = hass.data.setdefault(DOMAIN, {})
    if (coordinator := coordinators.get(network.name)) is None:
        coordinator = coordinators[network.name] = CitibikeCoordinator(hass, network)

    await coordinator.async_ensure_loaded()
    if coordinator.data is None:
        raise ConfigEntryNotReady(f"Could not fetch stations for {network.value}")

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Drop the coordinator once no other loaded entry uses its network
        network = entry.runtime_data.network
        if not any(
            other.entry_id != entry.entry_id
            and other.state is ConfigEntryState.LOADED
            and other.data["network"] == network.value
            for other in hass.config_entries.async_entries(DOMAIN)
        ):
            hass.data[DOMAIN].pop(network.name, None)

    return unload_ok
