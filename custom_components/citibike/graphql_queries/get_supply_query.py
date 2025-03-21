"""GraphQL query for fetching Citibike supply data."""

GET_SUPPLY_QUERY = """
    query GetSupply($input: SupplyInput) {
        supply(input: $input) {
            stations {
                stationName
                location {
                    lat
                    lng
                }
                siteId
                totalBikesAvailable
                bikeDocksAvailable
                lastUpdatedMs
                bikesAvailable
                ebikesAvailable
                isOffline
                totalRideablesAvailable
                ebikes {
                    rideableName
                    batteryStatus {
                        percent
                        distanceRemaining {
                            value
                            unit
                        }
                    }
                }
            }
        }
    }
"""
