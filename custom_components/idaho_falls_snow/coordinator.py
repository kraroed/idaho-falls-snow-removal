"""Data coordinator for Idaho Falls snow-removal data."""

import asyncio
import html
import logging
import re
from collections import Counter

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    LAYER_PARKING,
    LAYER_PLOWED_METHOD,
    LAYER_PLOWED_PRIORITY,
    LAYER_PRIORITY_STATUS,
    LAYER_ZONE_STATUS,
    LAYER_ZONES,
    SNOW_MAP_URL,
    SNOW_PAGE_URL,
)
from .parsing import completed, updated_date, working, zone_key

_LOGGER = logging.getLogger(__name__)

ALIASES = {
    "zone": ("Zone", "ZONE", "ZoneNumber", "ZONE_NUMBER"),
    "zone_number": ("ZoneNumber", "ZONE_NUMBER", "Zone", "ZONE"),
    "last_plow": ("LastPlowDate", "LASTPLOWDATE"),
    "planned": ("PlannedPlowDate", "PLANNEDPLOWDATE"),
    "planned_ns": ("PlannedPlowDateNS", "PLANNEDPLOWDATENS"),
    "planned_ew": ("PlannedPlowDateEW", "PLANNEDPLOWDATEEW"),
    "status": ("SnowRemovalStatus", "SNOWREMOVALSTATUS", "Status", "STATUS"),
    "priority": ("Priority", "PRIORITY"),
    "method": ("PlowMethod", "PLOWMETHOD", "Method", "METHOD"),
    "agency": ("PlowAgency", "PLOWAGENCY", "Agency", "AGENCY"),
    "parking": ("ParkingRestriction", "PARKINGRESTRICTION"),
}


def value(row, key, default=None):
    """Read a GIS attribute while tolerating known field-name variants."""
    for field in ALIASES.get(key, (key,)):
        if field in row and row[field] not in (None, ""):
            return row[field]
    return default


class IdahoFallsSnowCoordinator(DataUpdateCoordinator):
    """Fetch and normalize the City's snow-removal sources."""

    def __init__(self, hass, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            always_update=False,
        )
        self.session = None

    async def _async_update_data(self):
        try:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()

            page = await self._page()
            layer_specs = (
                ("zones", LAYER_ZONES),
                ("priority_status", LAYER_PRIORITY_STATUS),
                ("zone_status", LAYER_ZONE_STATUS),
                ("plowed_priority", LAYER_PLOWED_PRIORITY),
                ("plowed_method", LAYER_PLOWED_METHOD),
                ("parking", LAYER_PARKING),
            )
            results = await asyncio.gather(
                *(self._layer(layer_id) for _, layer_id in layer_specs),
                return_exceptions=True,
            )
            failures = [
                f"{name}: {result}"
                for (name, _), result in zip(layer_specs, results)
                if isinstance(result, Exception)
            ]
            if failures:
                raise UpdateFailed(
                    "Unable to refresh all Idaho Falls GIS layers; "
                    + "; ".join(failures)
                )

            data = {
                name: result
                for (name, _), result in zip(layer_specs, results)
            }
            priority_status = data["priority_status"]
            zone_status = data["zone_status"]
            plowed_priority = data["plowed_priority"]
            plowed_method = data["plowed_method"]
            parking = data["parking"]

            zones = {}
            for row in zone_status or data["zones"]:
                raw_zone = value(row, "zone", value(row, "zone_number"))
                key = zone_key(raw_zone)
                zones[key] = {
                    "zone": {
                        "downtown": "Downtown",
                        "a": "Zone A",
                        "b": "Zone B",
                    }.get(key, str(raw_zone or "Unknown Zone")),
                    "zone_number": value(row, "zone_number", raw_zone),
                    "status": value(row, "status", "unknown"),
                    "last_plow": value(row, "last_plow"),
                    "planned_plow": value(row, "planned"),
                    "planned_plow_ns": value(row, "planned_ns"),
                    "planned_plow_ew": value(row, "planned_ew"),
                }

            data.update(
                {
                    "active": bool(
                        sum(working(value(row, "status")) for row in priority_status)
                        or sum(working(value(row, "status")) for row in zone_status)
                        or page["parking_restrictions"] is True
                    ),
                    "working_streets": sum(
                        working(value(row, "status")) for row in priority_status
                    ),
                    "completed_streets": sum(
                        completed(value(row, "status")) for row in priority_status
                    ),
                    "working_zones": sum(
                        working(value(row, "status")) for row in zone_status
                    ),
                    "completed_zones": sum(
                        completed(value(row, "status")) for row in zone_status
                    ),
                    "priority_counts": dict(
                        Counter(str(value(row, "priority", "unknown")) for row in plowed_priority)
                    ),
                    "method_counts": dict(
                        Counter(str(value(row, "method", "unknown")) for row in plowed_method)
                    ),
                    "agency_counts": dict(
                        Counter(str(value(row, "agency", "unknown")) for row in plowed_method)
                    ),
                    "parking_restriction_segments": len(parking),
                    "zones": zones,
                    "city_page": page,
                    "source_url": SNOW_PAGE_URL,
                    "map_url": SNOW_MAP_URL,
                    "fetched_at": dt_util.utcnow().isoformat(),
                }
            )
            return data
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(
                f"Unable to reach or parse Idaho Falls snow sources: {err}"
            ) from err

    async def _layer(self, layer_id):
        """Fetch one ArcGIS layer and reject malformed responses."""
        async with self.session.get(
            f"{SNOW_MAP_URL}/{layer_id}/query",
            params={
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json",
            },
            timeout=30,
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)

        if "error" in payload:
            raise RuntimeError(payload["error"])
        if not isinstance(payload.get("features"), list):
            raise RuntimeError(f"Layer {layer_id} response did not contain a features list")
        return [
            feature.get("attributes", {})
            for feature in payload["features"]
            if isinstance(feature, dict)
        ]

    async def _page(self):
        """Fetch the City's public snow-removal status page."""
        async with self.session.get(SNOW_PAGE_URL, timeout=30) as response:
            response.raise_for_status()
            body = await response.text()

        page_text = re.sub(
            r"\\s+",
            " ",
            html.unescape(BeautifulSoup(body, "html.parser").get_text(" ", strip=True)),
        )
        parking_match = re.search(
            r"parking restrictions are (not )?in place", page_text, re.IGNORECASE
        )
        return {
            "updated": updated_date(page_text),
            "parking_restrictions": (
                False
                if parking_match and parking_match.group(1)
                else True
                if parking_match
                else None
            ),
        }

    async def async_shutdown(self):
        """Close the HTTP session when the config entry is unloaded."""
        if self.session is not None and not self.session.closed:
            await self.session.close()
        self.session = None
