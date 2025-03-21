"""GraphQL query for initializing Citibike stations."""

GET_INIT_STATION_QUERY = """
    query GetSupply($input: SupplyInput) {
        supply(input: $input) {
            stations {
                stationName
                location {
                    lat
                    lng
                }
            }
        }
    }
"""
