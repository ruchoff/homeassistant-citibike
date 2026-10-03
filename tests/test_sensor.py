"""Tests for the Citibike coordinator and sensor."""

from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.citibike.const import DOMAIN
from custom_components.citibike.graphql_requests import GraphQLRequestError
from custom_components.citibike.sensor import SENSOR_DESCRIPTIONS

from .conftest import STATIONS, make_station

ENTITY_ID = "sensor.citibike_e_40_st_park_ave"


def make_entry(
    station_id: str = "motivate_BKN_1", station_name: str = "E 40 St & Park Ave"
) -> MockConfigEntry:
    """Build a config entry for a station."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "network": "Citibike",
            "station_id": station_id,
            "station_name": station_name,
        },
        unique_id=f"citibike_{station_id}",
        minor_version=2,
    )


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up a config entry."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def tick(hass: HomeAssistant) -> None:
    """Advance past one update interval."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5, seconds=1))
    await hass.async_block_till_done()


async def test_sensor_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_fetch,
) -> None:
    """The sensor reports the station's rideables and attributes."""
    await setup_entry(hass, make_entry())

    state = hass.states.get(ENTITY_ID)
    assert state.state == "7"
    assert state.attributes["station_id"] == "6432.11"
    assert state.attributes["docks_available"] == 10
    assert state.attributes["station_capacity"] == 17
    assert state.attributes["max_ebike_distance"] == 35
    assert state.attributes["available_bike_types"] == {
        "Human Powered": 5,
        "Electric Powered": 2,
    }
    assert state.attributes["last_reported"] == datetime(
        2025, 1, 1, 22, 59, 59, tzinfo=UTC
    )
    assert state.attributes["friendly_name"] == "Citibike E 40 St & Park Ave"
    assert state.attributes["unit_of_measurement"] == "rideables"
    assert state.attributes["state_class"] == "measurement"

    entity = entity_registry.async_get(ENTITY_ID)
    assert entity.unique_id == "citibike_motivate_BKN_1"
    device = device_registry.async_get(entity.device_id)
    assert device.name == "Citibike E 40 St & Park Ave"


async def test_updates_every_interval(hass: HomeAssistant, mock_fetch) -> None:
    """Every poll fetches fresh data."""
    await setup_entry(hass, make_entry())
    assert mock_fetch.call_count == 1

    mock_fetch.return_value = [
        make_station(
            "E 40 St & Park Ave", "motivate_BKN_1", 0, 0, totalRideablesAvailable=3
        )
    ]
    await tick(hass)
    assert mock_fetch.call_count == 2
    assert hass.states.get(ENTITY_ID).state == "3"

    await tick(hass)
    assert mock_fetch.call_count == 3


async def test_stations_share_one_fetch(hass: HomeAssistant, mock_fetch) -> None:
    """Two stations on a network use a single request per poll."""
    await setup_entry(hass, make_entry())
    await setup_entry(hass, make_entry("motivate_BKN_2", "W 21 St & 6 Ave"))
    assert mock_fetch.call_count == 1

    await tick(hass)
    assert mock_fetch.call_count == 2


async def test_unavailable_on_failure(hass: HomeAssistant, mock_fetch) -> None:
    """A failed fetch or a missing station makes the sensor unavailable."""
    await setup_entry(hass, make_entry())

    mock_fetch.side_effect = GraphQLRequestError("boom")
    await tick(hass)
    assert hass.states.get(ENTITY_ID).state == "unavailable"

    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS
    await tick(hass)
    assert hass.states.get(ENTITY_ID).state == "7"

    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS[1:]
    await tick(hass)
    assert hass.states.get(ENTITY_ID).state == "unavailable"


async def test_setup_retry_and_unload(hass: HomeAssistant, mock_fetch) -> None:
    """Setup retries when the first fetch fails, and entries unload cleanly."""
    mock_fetch.side_effect = GraphQLRequestError("boom")
    entry = make_entry()
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY

    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert hass.data[DOMAIN] == {}


async def test_station_rename(hass: HomeAssistant, mock_fetch) -> None:
    """A renamed station keeps working because it is tracked by ID."""
    await setup_entry(hass, make_entry())

    mock_fetch.return_value = [
        make_station("Park Ave & E 40 St", "motivate_BKN_1", 0, 0)
    ]
    await tick(hass)

    state = hass.states.get(ENTITY_ID)
    assert state.state == "7"
    assert state.attributes["station_name"] == "Park Ave & E 40 St"


def make_legacy_entry() -> MockConfigEntry:
    """Build a config entry as created before station IDs were stored."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"network": "Citibike", "id": "E 40 St & Park Ave"},
        unique_id="citibike_e 40 st & park ave",
    )


async def test_migrate_station_name(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_fetch
) -> None:
    """An entry configured by station name is migrated to the station ID."""
    entry = make_legacy_entry()
    entry.add_to_hass(hass)
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "E 40 St & Park Ave",
        suggested_object_id="my_station",
        config_entry=entry,
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.minor_version == 2
    assert entry.unique_id == "citibike_motivate_BKN_1"
    assert entry.data == {
        "network": "Citibike",
        "station_id": "motivate_BKN_1",
        "station_name": "E 40 St & Park Ave",
    }
    # The existing entity keeps its entity ID under the new unique ID
    assert (
        entity_registry.async_get("sensor.my_station").unique_id
        == "citibike_motivate_BKN_1"
    )
    assert hass.states.get("sensor.my_station").state == "7"
    assert len(
        er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    ) == 1 + len(SENSOR_DESCRIPTIONS)


async def test_migrate_missing_station(hass: HomeAssistant, mock_fetch) -> None:
    """An entry whose station name no longer exists fails setup untouched."""
    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS[1:]
    entry = make_legacy_entry()
    await setup_entry(hass, entry)

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.data == {"network": "Citibike", "id": "E 40 St & Park Ave"}


async def test_station_value_sensors(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_fetch
) -> None:
    """Each station value has its own sensor on the station device."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    await setup_entry(hass, make_entry())

    expected = {
        "docks_available": "10",
        "classic_bikes_available": "5",
        "e_bikes_available": "2",
        "max_e_bike_range": "35",
    }
    for suffix, value in expected.items():
        assert hass.states.get(f"{ENTITY_ID}_{suffix}").state == value

    main = entity_registry.async_get(ENTITY_ID)
    for suffix in expected:
        entity = entity_registry.async_get(f"{ENTITY_ID}_{suffix}")
        assert entity.device_id == main.device_id

    mock_fetch.return_value = [
        make_station("E 40 St & Park Ave", "motivate_BKN_1", 0, 0, ebikes=[])
    ]
    await tick(hass)
    assert hass.states.get(f"{ENTITY_ID}_max_e_bike_range").state == "0"

    mock_fetch.side_effect = GraphQLRequestError("boom")
    await tick(hass)
    assert hass.states.get(f"{ENTITY_ID}_docks_available").state == "unavailable"
