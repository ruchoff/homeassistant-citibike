"""Constants for the Citibike integration."""

from enum import Enum

DOMAIN = "citibike"

CONF_STATIONID = "id"


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
    CITIBIKE = "BKN"
    BAYWHEELS = "SFO"
    DIVVY = "CHI"
    COGO = "CMH"
    CAPITALBIKESHARE = "DCA"
    BIKETOWN = "PDX"
