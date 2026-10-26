from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import IdahoFallsSnowCoordinator
PLATFORMS=[Platform.BINARY_SENSOR,Platform.SENSOR,Platform.BUTTON]
async def async_setup_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    c=IdahoFallsSnowCoordinator(hass,timedelta(minutes=entry.options.get(CONF_SCAN_INTERVAL,entry.data.get(CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL))))
    await c.async_config_entry_first_refresh()
    entry.runtime_data=c
    await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS)
    return True
async def async_unload_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    return await hass.config_entries.async_unload_platforms(entry,PLATFORMS)
