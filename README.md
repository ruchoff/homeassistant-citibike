# Home Assistant Citi Bike Station Status Sensor
[![hacs][hacs-badge]][hacs]
[![GitHub Release][release-badge]][release-url]
[![HACS validation][hacs-validation-badge]][hacs-validation-url]
[![HASSFEST validation][hassfest-validation-badge]][hassfest-validation-url]
[![license][license-badge]][license-url]


This integration provides real-time data about bike share stations across multiple city networks within Home Assistant. It allows you to track bike availability, docking spaces, and station status for a variety of bike share programs, including Citi Bike, Bay Wheels, Divvy, CoGo, Capital Bikeshare, and BIKETOWN. By fetching information from each city's official GraphQL feed, it helps you stay up to date with the availability of bikes in real-time.

## Supported Networks:
- [**Bay Wheels**][baywheels-home] - _Bay Area_
- [**BIKETOWN**][biketown-home] - _Portland_
- [**Capital Bikeshare**][capitalbikeshare-home] - _Metro DC_
- [**Citi Bike**][citibike-home] - _New York_
- [**CoGo**][cogo-home] - _Columbus_
- [**Divvy**][divvy-home] - _Chicago_



## Features
- Track the number of available bikes and docking spaces at each station
- Separate sensors for docks, classic bikes, e-bikes and e-bike range, ready for graphs and automations
- Monitor station status, including whether bikes are available for renting and if the station is accepting bike returns
- Display additional station attributes, such as location, capacity, and availability of bike types
- Automatically updates data at regular intervals to provide real-time information
- Choose from multiple bike share networks and view station details within the selected network
- Station selection list is sorted by distance to your Home Zone for easy setup
- One request per network per update, shared by all the stations you monitor on it

## Installation
### HACS (Home Assistant Community Store)
[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruchoff&repository=homeassistant-citibike)

### Manual Installation

1. Download the `citibike` folder from this repository.
2. Copy the `citibike` folder into your `custom_components` directory in Home Assistant.


### Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for "Citi Bike".
3. Select the **Network** you want to track (e.g., Citibike, Bay Wheels, Divvy, CoGo, Capital Bikeshare, or BIKETOWN).
4. After selecting the network, a dropdown will appear with a list of stations within that network. Choose the station you want to monitor.

Repeat these steps for each station you want to track. Each station is added as a device.



## Sensors

Each station provides the following sensors. Data is updated every 5 minutes, and the sensors become unavailable if the network cannot be reached or no longer reports the station.

| **Sensor**                  | **Description**                                                              | **Unit**    |
|-----------------------------|------------------------------------------------------------------------------|-------------|
| **Station** (main sensor)   | The total number of rideables (bikes and e-bikes) available for rent.        | `rideables` |
| **Docks available**         | The number of available docking spaces at the station.                       | `docks`     |
| **Classic bikes available** | The number of human powered bikes available for rent.                        | `bikes`     |
| **E-bikes available**       | The number of e-bikes available for rent.                                    | `bikes`     |
| **Max e-bike range**        | The longest remaining range of the e-bikes at the station (`0` if none).     | `mi`        |

### Main Sensor Attributes:
The main sensor also includes the following attributes:

| **Attribute**              | **Description**                                                                                           | **Example**            |
|----------------------------|-----------------------------------------------------------------------------------------------------------|------------------------|
| **station_id**              | The unique identifier for the station.                                                                     | `6432.11`              |
| **station_name**            | The name or location of the station.                                                                       | `E 40 St & Park Ave`   |
| **network**                 | The name of the bike share network of the station.                                                   | `Citibike`             |
| **latitude**                | The latitude coordinate of the station.                                                                   | `40.748817`            |
| **longitude**               | The longitude coordinate of the station.                                                                  | `-73.985428`           |
| **total_rideables_available** | The total number of rideables (bikes and e-bikes) available for rent.                                     | `23`                   |
| **station_capacity**        | The number of bikes and open docks currently at the station.                                               | `40`                   |
| **docks_available**         | The number of available docking spaces at the station.                                                   | `10`                   |
| **available_bike_types**    | The number of bikes available for rent by type.                                                           | `Human Powered: 7, Electric Powered: 16` |
| **max_ebike_distance**      | The maximum distance that an e-bike at this station can travel, based on the remaining battery life.                       | `35`                   |
| **ebike_status**            | The status of each available e-bike, including battery percentage and remaining distance. Not stored in history. | `bike_id: ...0123, battery_percent: 99, distance_remaining: 35, distance_remaining_units: miles` |
| **last_reported**           | The timestamp when the station's data was last updated.                                                   | `2025-01-01T23:59:59+00:00` |
| **is_offline**              | Indicates whether the station is offline (True/False).                                                     | `False`                |



## Acknowledgements

This integration uses data from each network's system, which is provided via each's respective GraphQL Feed. Special thanks to Lyft Bikes and Scooters, LLC for providing this data to the public under their Data License Agreement.
### GraphQL Feeds
- [**Bay Wheels**][baywheels-gql]
- [**BIKETOWN**][biketown-gql]
- [**Capital Bikeshare**][capitalbikeshare-gql]
- [**Citi Bike**][citibike-gql]
- [**CoGo**][cogo-gql]
- [**Divvy**][divvy-gql]

### Data License Agreements
- [**Bay Wheels**][baywheels-data-license]
- [**BIKETOWN**][biketown-data-license]
- [**Capital Bikeshare**][capitalbikeshare-data-license]
- [**Citi Bike**][citibike-data-license]
- [**CoGo**][cogo-data-license]
- [**Divvy**][divvy-data-license]


**Important:** This integration is not affiliated with or endorsed by Bikeshare (Lyft Bikes and Scooters, LLC) or Citigroup, Inc., and the data is provided "as is" without warranties regarding its availability or accuracy.


<!-- Badges -->
[hacs-badge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg
[hacs-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/validate.yml?label=HACS%20Validation
[hassfest-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/hassfest.yml?label=Hassfest%20Validation
[license-badge]: https://img.shields.io/github/license/ruchoff/homeassistant-citibike
[release-badge]: https://img.shields.io/github/v/release/ruchoff/homeassistant-citibike

<!-- URLs -->
[baywheels-home]: https://www.lyft.com/bikes/bay-wheels
[biketown-home]: https://biketownpdx.com/
[capitalbikeshare-home]: https://capitalbikeshare.com/
[citibike-home]: https://citibikenyc.com/
[cogo-home]: https://cogobikeshare.com/
[divvy-home]: https://divvybikes.com/



[baywheels-data-license]: https://baywheels-assets.s3.amazonaws.com/data-license-agreement.html
[biketown-data-license]: https://biketownpdx.com/system-data
[capitalbikeshare-data-license]: https://capitalbikeshare.com/data-license-agreement
[citibike-data-license]: https://ride.citibikenyc.com/data-sharing-policy
[cogo-data-license]: https://cogobikeshare.com/data-license-agreement
[divvy-data-license]: https://divvybikes.com/data-license-agreement

[baywheels-gql]: https://account.baywheels.com/bikesharefe-gql
[biketown-gql]: https://biketownpdx.com/bikesharefe-gql
[capitalbikeshare-gql]: https://capitalbikeshare.com/bikesharefe-gql
[citibike-gql]: https://account.citibikenyc.com/bikesharefe-gql
[cogo-gql]: https://cogobikeshare.com/bikesharefe-gql
[divvy-gql]: https://divvybikes.com/bikesharefe-gql

[hacs]: https://hacs.xyz
[hacs-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/validate.yml
[hassfest-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/hassfest.yml
[home-assistant]: https://www.home-assistant.io/
[license-url]: https://github.com/ruchoff/homeassistant-citibike/blob/main/LICENSE

[release-url]: https://github.com/ruchoff/homeassistant-citibike/releases
