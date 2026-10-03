"""Tests for the Citibike config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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
        result["flow_id"], {"network": "Citibike"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"
    # Closest station to home is offered first
    options = result["data_schema"].schema["station_id"].container
    assert list(options.values()) == ["W 21 St & 6 Ave", "E 40 St & Park Ave"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": "motivate_BKN_1"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Citibike E 40 St & Park Ave"
    assert result["data"] == {
        "network": "Citibike",
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
        result["flow_id"], {"network": "Citibike"}
    )
    assert result["step_id"] == "select_station"


async def test_cannot_connect_then_recover(hass: HomeAssistant, mock_fetch) -> None:
    """A failed station fetch shows an error and can be retried."""
    mock_fetch.side_effect = GraphQLRequestError("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "Citibike"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_fetch.side_effect = None
    mock_fetch.return_value = STATIONS
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "Citibike"}
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
        result["flow_id"], {"network": "Bay Wheels"}
    )
    assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"network": "Bay Wheels"}
    )
    assert result["step_id"] == "select_station"
    assert len(result["data_schema"].schema["station_id"].container) == 2


async def test_already_configured(hass: HomeAssistant, mock_fetch) -> None:
    """The same station cannot be added twice."""
    for expected in (FlowResultType.CREATE_ENTRY, FlowResultType.ABORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": "Citibike"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": "motivate_BKN_1"}
        )
        await hass.async_block_till_done()
        assert result["type"] is expected

    assert result["reason"] == "already_configured"


async def test_same_station_name_on_another_network(
    hass: HomeAssistant, mock_fetch
) -> None:
    """A station name shared by two networks can be added on both."""
    for network in ("Citibike", "Divvy"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": network}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": "motivate_BKN_1"}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_station_names(hass: HomeAssistant, mock_fetch) -> None:
    """Two stations sharing a name are both offered and can both be added."""
    mock_fetch.return_value = [
        make_station("Clinton St & Grand St", "motivate_BKN_1", 40.71, -73.98),
        make_station("Clinton St & Grand St", "motivate_BKN_2", 40.72, -73.99),
    ]

    for station_id in ("motivate_BKN_1", "motivate_BKN_2"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"network": "Citibike"}
        )
        assert len(result["data_schema"].schema["station_id"].container) == 2
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"station_id": station_id}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
