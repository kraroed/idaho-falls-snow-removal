from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN,MANUFACTURER
async def async_setup_entry(hass,entry,async_add_entities):
    c=entry.runtime_data; es=[]
    for k,n,g in [("removal_status","Snow Removal Status",lambda d:"active" if d["active"] else "idle"),("removal_alert","Snow Removal Alert",lambda d:"Active snow-removal operations" if d["active"] else "No active operations"),("working_zones","Working Zones",lambda d:d["working_zones"]),("completed_zones","Completed Zones",lambda d:d["completed_zones"]),("working_streets","Working Streets",lambda d:d["working_streets"]),("completed_streets","Completed Streets",lambda d:d["completed_streets"]),("parking_restriction_segments","Parking Restriction Street Segments",lambda d:d["parking_restriction_segments"])]:
        es.append(Snow(c,k,n,g))
    for p in (1,2,3): es.append(Snow(c,f"priority_{p}_streets",f"Priority {p} Streets",lambda d,p=p:d["priority_counts"].get(str(p),0)))
    for k,n in (("downtown","Downtown"),("a","Zone A"),("b","Zone B")): es.append(Zone(c,k,n))
    async_add_entities(es)
class Base(SensorEntity):
    _attr_has_entity_name=True
    def __init__(self,c):
        self.c=c; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,"idaho_falls")},name="Idaho Falls Snow Removal",manufacturer=MANUFACTURER,model="City snow GIS",configuration_url=c.data["map_url"])
class Snow(Base):
    def __init__(self,c,k,n,g): super().__init__(c); self.g=g; self._attr_name=n; self._attr_unique_id=f"idaho_falls_snow_{k}"; self._attr_native_unit_of_measurement="segments" if "streets" in k or "segments" in k else "zones" if "zones" in k else None
    @property
    def native_value(self): return self.g(self.c.data)
    @property
    def extra_state_attributes(self): return {"source_url":self.c.data["source_url"],"map_url":self.c.data["map_url"],"city_page_updated":self.c.data["city_page"]["updated"],"city_parking_restrictions":self.c.data["city_page"]["parking_restrictions"]}
class Zone(Base):
    def __init__(self,c,k,n): super().__init__(c); self.k=k; self._attr_name=n; self._attr_unique_id=f"idaho_falls_snow_{k}"
    @property
    def native_value(self): return self.c.data["zones"].get(self.k,{}).get("status","unknown")
    @property
    def extra_state_attributes(self): return {**self.c.data["zones"].get(self.k,{}),"source_url":self.c.data["source_url"],"map_url":self.c.data["map_url"],"plow_method_counts":self.c.data["method_counts"],"plow_agency_counts":self.c.data["agency_counts"]}
