"""Constants for the Citibike integration."""

from dataclasses import dataclass
from datetime import timedelta

DOMAIN = "citibike"

CONF_NETWORK = "network"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
# Entries created before station IDs were stored only hold the station name
CONF_LEGACY_STATION_NAME = "id"

UPDATE_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True)
class Network:
    """A bike share network served by a Lyft GraphQL endpoint."""

    key: str
    name: str
    endpoint: str
    regions: tuple[str, ...]


NETWORKS: tuple[Network, ...] = (
    Network(
        key="citibike",
        name="Citibike",
        endpoint="https://account.citibikenyc.com/bikesharefe-gql",
        regions=("BKN",),
    ),
    Network(
        key="baywheels",
        name="Bay Wheels",
        endpoint="https://account.baywheels.com/bikesharefe-gql",
        regions=("SFO", "SJC"),
    ),
    Network(
        key="divvy",
        name="Divvy",
        endpoint="https://divvybikes.com/bikesharefe-gql",
        regions=("CHI",),
    ),
    Network(
        key="capitalbikeshare",
        name="Capital Bikeshare",
        endpoint="https://capitalbikeshare.com/bikesharefe-gql",
        regions=("DCA",),
    ),
    Network(
        key="biketown",
        name="BIKETOWN",
        endpoint="https://biketownpdx.com/bikesharefe-gql",
        regions=("PDX",),
    ),
)

NETWORKS_BY_KEY: dict[str, Network] = {network.key: network for network in NETWORKS}

# Entries used to store the network by the display name it had at the time
LEGACY_NETWORK_KEYS: dict[str, str] = {
    "Citibike": "citibike",
    "Bay Wheels": "baywheels",
    "Divvy": "divvy",
    "Capital Bikeshare": "capitalbikeshare",
    "BIKETOWN": "biketown",
}
