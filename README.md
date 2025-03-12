# Home Assistant CitiBike Station Status Sensor
[![hacs][hacs-badge]][hacs]
[![GitHub Release][release-badge]][release-url]
[![HACS validation][hacs-validation-badge]][hacs-validation-url]
[![HASSFEST validation][hassfest-validation-badge]][hassfest-validation-url]
[![license][license-badge]][license-url]


This integration provides real-time data about NYC Citi Bike stations within Home Assistant. By fetching information from the official Citi Bike GBFS feed, it monitors available bikes, docking spaces, and station status, helping you track bike availability in real-time.

## Features
- Track the number of available bikes and docking spaces at each station
- Monitor station status, including whether bikes are available for renting and if the station is accepting bike returns
- Display additional station attributes, such as location, capacity, and availability of bike types
- Automatically updates data at regular intervals to provide real-time information

## Installation
### HACS (Home Assistant Community Store)
[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruchoff&repository=homeassistant-citibike)

### Manual Installation

1. Download the `citibike` folder from this repository.
2. Copy the `citibike` folder into your `custom_components` directory in Home Assistant.


### Configuration

1. In Home Assistant, navigate to **Configuration** > **Devices & Services**.
2. Click **Add Integration** and search for "CitiBike".
3. Enter the **Station ID** for the CitiBike station you want to monitor. You can find this ID on [CitiBike's Explore page](https://citibikenyc.com/explore). Simply select a station on the map, and the Site ID will appear at the bottom of the information card.



## Sensor State and Attributes

### Sensor State:
- The state of the sensor will display the number of available bikes at the station.

### Sensor Attributes:
Each sensor will include the following attributes:

| **Attribute**              | **Description**                                                                                           | **Example**            |
|----------------------------|-----------------------------------------------------------------------------------------------------------|------------------------|
| **station_id**              | The unique identifier for the station.                                                                     | `6432.11`              |
| **station_name**            | The name or location of the station.                                                                       | `E 40 St & Park Ave`   |
| **latitude**                | The latitude coordinate of the station.                                                                   | `40.748817`            |
| **longitude**               | The longitude coordinate of the station.                                                                  | `-73.985428`           |
| **station_capacity**        | The total number of docking spaces available at the station.                                               | `40`                   |
| **last_reported**           | The timestamp when the station's data was last updated.                                                   | `2025-01-01T23:59:59` |
| **docks_available**         | The number of available docking spaces at the station.                                                   | `10`                   |
| **is_renting**              | Indicates whether the station is currently renting bikes (True/False).                                     | `True`                 |
| **is_returning**            | Indicates whether the station is currently accepting bike returns (True/False).                           | `True`                 |
| **total_rideables_available** | The total number of rideables (bikes and e-bikes) available for rent.                                     | `23`                   |
| **available_bike_types**    | The types of bikes available for rent (e.g., "Human Powered" and "Electric Powered").                     | `Human Powered: 7, Electric Powered: 16` |
| **max_ebike_distance**      | The maximum distance that an e-bike can travel, based on the remaining battery life.                       | `35 miles`             |
| **ebike_status**            | The status of each available e-bike, including battery percentage and remaining distance.                 | `bike_id: ...0123, battery_percent: 99, distance_remaining: 35 miles` |
| **is_offline**              | Indicates whether the station is offline (True/False).                                                     | `False`                |


## Acknowledgements

This integration uses data from the CitiBike system, which is provided via the [CitiBike GraphQL Feed][citibike-gql]. Special thanks to Lyft Bikes and Scooters, LLC for providing this data to the public under their [Data License Agreement][citibike-data-license].

**Important:** This integration is not affiliated with or endorsed by Bikeshare (Lyft Bikes and Scooters, LLC) or Citigroup, Inc., and the data is provided "as is" without warranties regarding its availability or accuracy.


<!-- Badges -->
[hacs-badge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg
[hacs-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/validate.yml?label=HACS%20Validation
[hassfest-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/hassfest.yml?label=Hassfest%20Validation
[license-badge]: https://img.shields.io/github/license/ruchoff/homeassistant-citibike
[release-badge]: https://img.shields.io/github/v/release/ruchoff/homeassistant-citibike

<!-- URLs -->
[citibike-data-license]: https://ride.citibikenyc.com/data-sharing-policy
[citibike-explore]: https://citibikenyc.com/explore
[citibike-gql]: https://account.citibikenyc.com/bikesharefe-gql
[hacs]: https://hacs.xyz
[hacs-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/validate.yml
[hassfest-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/hassfest.yml
[home-assistant]: https://www.home-assistant.io/
[license-url]: https://github.com/ruchoff/homeassistant-citibike/blob/main/LICENSE

[release-url]: https://github.com/ruchoff/homeassistant-citibike/releases
