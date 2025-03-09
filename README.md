# Home Assistant CitiBike Station Status Sensor
[![hacs][hacs-badge]][hacs]
[![GitHub Release][release-badge]][release-url]
[![HACS validation][hacs-validation-badge]][hacs-validation-url]
[![HASSFEST validation][hassfest-validation-badge]][hassfest-validation-url]
[![license][license-badge]][license-url]


## Overview ##
This Home Assistant sensor provides real-time information about NYC Citi Bike stations. It fetches data from the official Citi Bike GBFS feed to monitor the number of available bikes, docks, and the overall station status. This can help you track bike availability in real-time for personal or community use.

## Sensor ##
A new sensor will be created for each station listed in your config.

### Sensor State ###
The state of the sensor is the number of bikes available.
### Sensor Attributes ###
The following attributes are provided for each sensor:


| **Attribute**              | **Description**                                                                                           | **Example**            |
|----------------------------|-----------------------------------------------------------------------------------------------------------|------------------------|
| **station_id**              | The unique identifier for the station.                                                                     | `6432.11`              |
| **latitude**                | The latitude coordinate of the station.                                                                   | `40.748817`            |
| **longitude**               | The longitude coordinate of the station.                                                                  | `-73.985428`           |
| **station_capacity**        | The total number of docking spaces available at the station.                                               | `40`                   |
| **last_reported**           | The timestamp when the station's data was last updated.                                                   | `2025-03-08 14:23:45` |
| **docks_available**         | The number of available docking spaces at the station.                                                   | `10`                   |
| **is_renting**              | Indicates whether the station is currently renting bikes. (True/False)                                    | `True`                 |
| **is_returning**            | Indicates whether the station is currently accepting bike returns. (True/False)                          | `True`                 |
| **num_bikes_available**     | The number of bikes currently available for rent.                                                        | `8`                    |
| **available_bike_types**    | The types of bikes available for rent. Includes "Human Powered" and "Electric Powered".                  | `Human Powered: 6, Electric Powered: 2` |
| **num_bikes_disabled**      | The number of bikes that are currently out of service at the station.                                      | `2`                    |
| **num_docks_disabled**      | The number of docking spaces that are currently unavailable at the station.                               | `1`                    |



## Installation ##
### HACS (Recommended) ##

CitiBike Station Status Sensor is available in [HACS][hacs] (Home Assistant Community Store).

Use this link to directly go to the repository in HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruchoff&repository=homeassistant-citibike)

_or_

1. Install HACS if you don't have it already
2. Open HACS in Home Assistant
3. Search for "CitiBike"
4. Click download.

### Manual ### 
Copy `citibike` folder to your `custom_components` folder in your Home Assistant configuration directory.

### Configuration ###
In your `configuration.yaml` file, add the following sensor:

```yaml
sensor:
  - platform: citibike
    stations:
      - id: "6432.11"
        name: "E 40 St & Park Ave"
```
`stations` accepts a list of one or many Citibike stations you want to track.
- `id` is a required field, and is the Site ID of the Citibike station you want to track. Getting the id is available on [Citibike's website][citibike-explore]. On the map, select the station and you will see `Site ID` at the bottom of the info card.

- `name` is optional. If omitted, sensor name will default to station's official name as provided in the API, with `citibike_station_` as the prefix.


<!-- Badges -->
[hacs-badge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg
[hacs-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/validate.yml?label=HACS%20Validation
[hassfest-validation-badge]: https://img.shields.io/github/actions/workflow/status/ruchoff/homeassistant-citibike/hassfest.yml?label=Hassfest%20Validation
[license-badge]: https://img.shields.io/github/license/ruchoff/homeassistant-citibike
[release-badge]: https://img.shields.io/github/v/release/ruchoff/homeassistant-citibike

<!-- URLs -->
[citibike-explore]: https://citibikenyc.com/explore
[hacs]: https://hacs.xyz
[hacs-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/validate.yml
[hassfest-validation-url]: https://github.com/ruchoff/homeassistant-citibike/actions/workflows/hassfest.yml
[home-assistant]: https://www.home-assistant.io/
[license-url]: https://github.com/ruchoff/homeassistant-citibike/blob/main/LICENSE

[release-url]: https://github.com/ruchoff/homeassistant-citibike/releases
