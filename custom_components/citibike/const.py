"""Constants for the Citibike integration."""

from datetime import timedelta
from enum import Enum

DOMAIN = "citibike"

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
# Entries created before station IDs were stored only hold the station name
CONF_LEGACY_STATION_NAME = "id"

UPDATE_INTERVAL = timedelta(minutes=5)


class NetworkNames(Enum):
    CITIBIKE = "Citibike"
    BAYWHEELS = "Bay Wheels"
    DIVVY = "Divvy"
    COGO = "CoGo"
    CAPITALBIKESHARE = "Capital Bikeshare"
    BIKETOWN = "BIKETOWN"


class NetworkGraphQLEndpoints(Enum):
    CITIBIKE = "https://account.citibikenyc.com/bikesharefe-gql"
    BAYWHEELS = "https://account.baywheels.com/bikesharefe-gql"
    DIVVY = "https://divvybikes.com/bikesharefe-gql"
    COGO = "https://cogobikeshare.com/bikesharefe-gql"
    CAPITALBIKESHARE = "https://capitalbikeshare.com/bikesharefe-gql"
    BIKETOWN = "https://biketownpdx.com/bikesharefe-gql"


class NetworkRegion(Enum):
    CITIBIKE = ["BKN"]
    BAYWHEELS = ["SFO", "SJC"]
    DIVVY = ["CHI"]
    COGO = ["CMH"]
    CAPITALBIKESHARE = ["DCA"]
    BIKETOWN = ["PDX"]
