import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from .const import DOMAIN,DEFAULT_SCAN_INTERVAL,MIN_SCAN_INTERVAL,MAX_SCAN_INTERVAL
class IdahoFallsSnowConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1
    async def async_step_user(self,user_input=None):
        if user_input is not None:return self.async_create_entry(title="Idaho Falls Snow Removal",data=user_input)
        return self.async_show_form(step_id="user",data_schema=vol.Schema({vol.Required(CONF_SCAN_INTERVAL,default=DEFAULT_SCAN_INTERVAL):vol.All(vol.Coerce(int),vol.Range(min=MIN_SCAN_INTERVAL,max=MAX_SCAN_INTERVAL))}))
    @staticmethod
    def async_get_options_flow(config_entry): return IdahoFallsSnowOptionsFlow()
class IdahoFallsSnowOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self,user_input=None):
        if user_input is not None:return self.async_create_entry(title="",data=user_input)
        current=self.config_entry.options.get(CONF_SCAN_INTERVAL,self.config_entry.data.get(CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL))
        return self.async_show_form(step_id="init",data_schema=vol.Schema({vol.Required(CONF_SCAN_INTERVAL,default=current):vol.All(vol.Coerce(int),vol.Range(min=MIN_SCAN_INTERVAL,max=MAX_SCAN_INTERVAL))}))
