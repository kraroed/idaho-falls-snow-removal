from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN,MANUFACTURER
async def async_setup_entry(hass,entry,async_add_entities): async_add_entities([SnowEvent(entry.runtime_data)])
class SnowEvent(BinarySensorEntity):
    _attr_has_entity_name=True; _attr_name="Snow Event"; _attr_unique_id="idaho_falls_snow_event"; _attr_icon="mdi:snowflake-alert"
    def __init__(self,c): self.c=c; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,"idaho_falls")},name="Idaho Falls Snow Removal",manufacturer=MANUFACTURER,model="City snow GIS",configuration_url=c.data["map_url"])
    @property
    def is_on(self): return self.c.data["active"]
    @property
    def extra_state_attributes(self): return {k:self.c.data[k] for k in ("working_streets","completed_streets","working_zones","completed_zones")}|{"city_page_updated":self.c.data["city_page"]["updated"],"city_parking_restrictions":self.c.data["city_page"]["parking_restrictions"],"source_url":self.c.data["source_url"],"map_url":self.c.data["map_url"]}
