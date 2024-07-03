# Home Assistant CitiBike Station Status Sensor
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

## Overview ##
A sensor to provide NYC Citi Bike Station status. The sensor pulls from the official Citi Bike GBFS Feed 

## Sensor ##
A new sensor will be created for each station listed in your config.

### Sensor State ###
The state of the sensor is the number of bikes available.
### Sensor Attributes ###
The following attributes are provided for each sensor:

- __station_id__
- __latitude__
- __longitude__
- __station_capacity__
- __last_reported__
- __docks_available__
- __is_renting__
- __is_returning__
- __num_bikes_available__
- __available_bike_types__
  - __Human Powered__
  - __Electric Powered__
- __num_bikes_disabled__
- __num_docks_disabled__

## Installation ##
### HACS (Recommended) ##
Add `https://github.com/ruchoff/homeassistant-citibike` to HACS Custom Repository. Download the CitiBike integration using HACS.

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
- `id` is a required field, and is the Site ID of the Citibike station you want to track. Getting the id is available on [Citibike's webside](https://citibikenyc.com/explore). On the map, select the station and you will see `Site ID` at the bottom of the info card.

- `name` is optional. If omitted, sensor name will default to station's official name as provided in the API, with `citibike_station_` as the prefix.
