GET_STATION_ID_QUERY = {
    "operationName": "GetSupply",
    "variables": {"input": {"regionCode": "BKN", "rideablePageLimit": 1000}},
    "query": """
            query GetSupply($input: SupplyInput) {
                supply(input: $input) {
                    stations {
                        siteId
                    }
                }
            }
        """,
}
