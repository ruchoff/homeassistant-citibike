import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_STATIONS, CONF_STATIONID, CONF_STATIONNAME

class CitibikeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        self._stations = []

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._stations.append(user_input)
            return self.async_create_entry(title="Citibike", data={CONF_STATIONS: self._stations})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_STATIONID): str,
                vol.Optional(CONF_STATIONNAME): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CitibikeOptionsFlowHandler(config_entry)

class CitibikeOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(CONF_STATIONS, default=self.config_entry.options.get(CONF_STATIONS, [])): vol.All(cv.ensure_list, [vol.Schema({
                vol.Required(CONF_STATIONID): str,
                vol.Optional(CONF_STATIONNAME): str,
            })]),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )
