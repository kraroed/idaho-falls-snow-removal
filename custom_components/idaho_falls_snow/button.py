from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN,MANUFACTURER
async def async_setup_entry(hass,entry,async_add_entities): async_add_entities([Refresh(entry.runtime_data)])
class Refresh(ButtonEntity):
    _attr_has_entity_name=True; _attr_name="Refresh"; _attr_unique_id="idaho_falls_snow_refresh"; _attr_icon="mdi:refresh"
    def __init__(self,c): self.c=c; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,"idaho_falls")},name="Idaho Falls Snow Removal",manufacturer=MANUFACTURER,model="City snow GIS",configuration_url=c.data["map_url"])
    async def async_press(self): await self.c.async_request_refresh()
