"""Tests for the Citibike config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.citibike.const import DOMAIN
from custom_components.citibike.graphql_requests import GraphQLRequestError

from .conftest import STATIONS, make_station


async def test_full_flow(hass: HomeAssistant, mock_fetch) -> None:
    """A network and station can be selected and set up."""
    hass.config.latitude = 40.7417
    hass.config.longitude = -73.9942

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"
    # Closest station to home is offered first
    options = result["data_schema"].schema["station_id"].config["options"]
    assert options == ["W 21 St & 6 Ave", "E 40 St & Park Ave"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": "E 40 St & Park Ave"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Citi Bike E 40 St & Park Ave"
    assert result["data"] == {
        "network": "citibike",
        "station_id": "motivate_BKN_1",
        "station_name": "E 40 St & Park Ave",
    }
    assert result["result"].unique_id == "citibike_motivate_BKN_1"


async def test_no_home_zone(hass: HomeAssistant, mock_fetch) -> None:
    """The flow does not depend on a zone.home entity."""
    hass.states.async_remove("zone.home")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["step_id"] == "select_station"


async def test_cannot_connect_then_recover(hass: HomeAssistant, mock_fetch) -> None:
    """A failed station fetch shows an error and can be retried."""
    mock_fetch.side_effect = GraphQLRequestError("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["step_id"] == "select_station"


async def test_partial_region_failure_is_not_cached(
    hass: HomeAssistant, mock_fetch
) -> None:
    """A network missing a region is reported instead of cached."""
    mock_fetch.side_effect = [
        STATIONS,
        GraphQLRequestError("boom"),
        STATIONS[:1],
        STATIONS[1:],
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "baywheels"}
    )
    assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "baywheels"}
    )
    assert result["step_id"] == "select_station"
    assert len(result["data_schema"].schema["station_id"].config["options"]) == 2


async def test_already_configured(hass: HomeAssistant, mock_fetch) -> None:
    """The same station cannot be added twice."""
    for expected in (FlowResultType.CREATE_ENTRY, FlowResultType.ABORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": "citibike"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": "E 40 St & Park Ave"}
        )
        await hass.async_block_till_done()
        assert result["type"] is expected

    assert result["reason"] == "already_configured"


async def test_same_station_name_on_another_network(
    hass: HomeAssistant, mock_fetch
) -> None:
    """A station name shared by two networks can be added on both."""
    for network in ("citibike", "divvy"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": network}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": "E 40 St & Park Ave"}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_station_names(hass: HomeAssistant, mock_fetch) -> None:
    """Two stations sharing a name are both offered and can both be added."""
    hass.config.latitude = 40.71
    hass.config.longitude = -73.98
    mock_fetch.return_value = [
        make_station("Clinton St & Grand St", "motivate_BKN_1", 40.71, -73.98),
        make_station("Clinton St & Grand St", "motivate_BKN_2", 40.72, -73.99),
    ]

    choices = {
        "Clinton St & Grand St": "motivate_BKN_1",
        "Clinton St & Grand St (2)": "motivate_BKN_2",
    }
    for choice, station_id in choices.items():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": "citibike"}
        )
        options = result["data_schema"].schema["station_id"].config["options"]
        assert options == list(choices)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": choice}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"]["station_id"] == station_id
        assert result["data"]["station_name"] == "Clinton St & Grand St"


async def test_typed_station(hass: HomeAssistant, mock_fetch) -> None:
    """Typed text must name a station; a typed station name is accepted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["data_schema"].schema["station_id"].config["custom_value"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": "not-a-station"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"
    assert result["errors"] == {"station_id": "invalid_station"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": " e 40 st & park ave"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["station_id"] == "motivate_BKN_1"
    assert result["data"]["station_name"] == "E 40 St & Park Ave"


async def test_station_list_is_fetched_per_flow(
    hass: HomeAssistant, mock_fetch
) -> None:
    """Each flow fetches the station list, so new stations show up."""
    for stations in (STATIONS[:1], STATIONS):
        mock_fetch.return_value = stations
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": "citibike"}
        )
        options = result["data_schema"].schema["station_id"].config["options"]
        assert len(options) == len(stations)


async def test_station_list_from_loaded_network(
    hass: HomeAssistant, mock_fetch
) -> None:
    """A network that is already set up provides the station list."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "network": "citibike",
            "station_id": "motivate_BKN_1",
            "station_name": "E 40 St & Park Ave",
        },
        unique_id="citibike_motivate_BKN_1",
        minor_version=3,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert mock_fetch.call_count == 1

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "citibike"}
    )
    assert result["step_id"] == "select_station"
    assert len(result["data_schema"].schema["station_id"].config["options"]) == 2
    assert mock_fetch.call_count == 1
    # Sorting the list for the flow leaves the sensor data alone
    assert "distance" not in hass.data[DOMAIN]["citibike"].data["motivate_BKN_1"]

    await hass.config_entries.async_unload(entry.entry_id)
