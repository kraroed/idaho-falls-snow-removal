import asyncio,html,re,logging
from collections import Counter
import aiohttp
from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator,UpdateFailed
from .const import *
_LOGGER=logging.getLogger(DOMAIN)
ALIASES={"zone":("Zone","ZONE","ZoneNumber","ZONE_NUMBER"),"zone_number":("ZoneNumber","ZONE_NUMBER","Zone","ZONE"),"last_plow":("LastPlowDate","LASTPLOWDATE"),"planned":("PlannedPlowDate","PLANNEDPLOWDATE"),"planned_ns":("PlannedPlowDateNS","PLANNEDPLOWDATENS"),"planned_ew":("PlannedPlowDateEW","PLANNEDPLOWDATEEW"),"status":("SnowRemovalStatus","SNOWREMOVALSTATUS","Status","STATUS"),"priority":("Priority","PRIORITY"),"method":("PlowMethod","PLOWMETHOD","Method","METHOD"),"agency":("PlowAgency","PLOWAGENCY","Agency","AGENCY"),"parking":("ParkingRestriction","PARKINGRESTRICTION")}
def value(row,key,default=None):
    for k in ALIASES.get(key,(key,)):
        if k in row and row[k] not in (None,""): return row[k]
    return default
def txt(v): return str(v or "").strip().lower()
def working(v): return any(x in txt(v) for x in ("working","in progress","active","plowing","started"))
def completed(v): return any(x in txt(v) for x in ("complete","completed","finished","done","plowed"))
def zkey(v):
    s=txt(v)
    if "downtown" in s or s=="dt": return "downtown"
    if s in {"a","zone a","1"} or s.endswith("zone a"): return "a"
    if s in {"b","zone b","2"} or s.endswith("zone b"): return "b"
    return s
class IdahoFallsSnowCoordinator(DataUpdateCoordinator):
    def __init__(self,hass,update_interval):
        super().__init__(hass,_LOGGER,name=DOMAIN,update_interval=update_interval,always_update=False); self.session=None
    async def _async_update_data(self):
        try:
            if self.session is None:self.session=aiohttp.ClientSession()
            page=await self._page()
            results=await asyncio.gather(*(self._layer(i) for i in (LAYER_ZONES,LAYER_PRIORITY_STATUS,LAYER_ZONE_STATUS,LAYER_PLOWED_PRIORITY,LAYER_PLOWED_METHOD,LAYER_PARKING)),return_exceptions=True)
            rows=[r if not isinstance(r,Exception) else [] for r in results]
            d=dict(zip(("zones","priority_status","zone_status","plowed_priority","plowed_method","parking"),rows))
            ps,zs,pp,pm,parking=d["priority_status"],d["zone_status"],d["plowed_priority"],d["plowed_method"],d["parking"]
            zones={}
            for r in zs or d["zones"]:
                raw=value(r,"zone",value(r,"zone_number")); key=zkey(raw)
                zones[key]={"zone":({"downtown":"Downtown","a":"Zone A","b":"Zone B"}.get(key,str(raw or "Unknown Zone"))),"zone_number":value(r,"zone_number",raw),"status":value(r,"status","unknown"),"last_plow":value(r,"last_plow"),"planned_plow":value(r,"planned"),"planned_plow_ns":value(r,"planned_ns"),"planned_plow_ew":value(r,"planned_ew")}
            d.update({"active":bool(sum(working(value(r,"status")) for r in ps) or sum(working(value(r,"status")) for r in zs) or page["parking_restrictions"] is True),"working_streets":sum(working(value(r,"status")) for r in ps),"completed_streets":sum(completed(value(r,"status")) for r in ps),"working_zones":sum(working(value(r,"status")) for r in zs),"completed_zones":sum(completed(value(r,"status")) for r in zs),"priority_counts":dict(Counter(str(value(r,"priority","unknown")) for r in pp)),"method_counts":dict(Counter(str(value(r,"method","unknown")) for r in pm)),"agency_counts":dict(Counter(str(value(r,"agency","unknown")) for r in pm)),"parking_restriction_segments":len(parking),"zones":zones,"city_page":page,"source_url":SNOW_PAGE_URL,"map_url":SNOW_MAP_URL})
            return d
        except (aiohttp.ClientError,asyncio.TimeoutError) as e: raise UpdateFailed(f"Unable to reach Idaho Falls snow sources: {e}") from e
    async def _layer(self,i):
        async with self.session.get(f"{SNOW_MAP_URL}/{i}/query",params={"where":"1=1","outFields":"*","returnGeometry":"false","f":"json"},timeout=30) as r:
            r.raise_for_status(); p=await r.json(content_type=None)
            if "error" in p: raise RuntimeError(p["error"])
            return [f.get("attributes",{}) for f in p.get("features",[])]
    async def _page(self):
        async with self.session.get(SNOW_PAGE_URL,timeout=30) as r:
            r.raise_for_status(); body=await r.text()
        s=re.sub(r"\s+"," ",html.unescape(BeautifulSoup(body,"html.parser").get_text(" ",strip=True)))
        u=re.search(r"Updated\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",s,re.I); p=re.search(r"parking restrictions are (not )?in place",s,re.I)
        return {"updated":u.group(1) if u else None,"parking_restrictions":False if p and p.group(1) else True if p else None}
    async def async_shutdown(self):
        if self.session: await self.session.close(); self.session=None
