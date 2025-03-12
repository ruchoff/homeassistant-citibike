GET_SUPPLY_QUERY = {
    "operationName": "GetSupply",
    "variables": {"input": {"regionCode": "BKN", "rideablePageLimit": 1000}},
    "query": """
        query GetSupply($input: SupplyInput) {
            supply(input: $input) {
                stations {
                    stationId
                    stationName
                    location {
                        lat
                        lng
                        __typename
                    }
                    bikesAvailable
                    bikeDocksAvailable
                    ebikesAvailable
                    scootersAvailable
                    totalBikesAvailable
                    totalRideablesAvailable
                    isOffline
                    siteId
                    ebikes {
                        rideableName
                        batteryStatus {
                            distanceRemaining {
                                value
                                unit
                                __typename
                            }
                            percent
                            __typename
                        }
                        __typename
                    }
                    scooters {
                        rideableName
                        batteryStatus {
                            distanceRemaining {
                                value
                                unit
                                __typename
                            }
                            percent
                            __typename
                        }
                        __typename
                    }
                    lastUpdatedMs
                    __typename
                }
            }
        }
    """,
}
