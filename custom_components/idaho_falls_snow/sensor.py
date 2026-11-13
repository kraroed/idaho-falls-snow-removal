"""Coordinator-backed sensors for Idaho Falls snow removal."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up snow-removal sensors."""
    coordinator = entry.runtime_data
    entities = []

    definitions = (
        ("removal_status", "Snow Removal Status", lambda data: "active" if data["active"] else "idle"),
        ("removal_alert", "Snow Removal Alert", lambda data: "Active snow-removal operations" if data["active"] else "No active operations"),
        ("working_zones", "Working Zones", lambda data: data["working_zones"]),
        ("completed_zones", "Completed Zones", lambda data: data["completed_zones"]),
        ("working_streets", "Working Streets", lambda data: data["working_streets"]),
        ("completed_streets", "Completed Streets", lambda data: data["completed_streets"]),
        ("parking_restriction_segments", "Parking Restriction Street Segments", lambda data: data["parking_restriction_segments"]),
    )
    for key, name, value_fn in definitions:
        entities.append(SnowSensor(coordinator, key, name, value_fn))

    for priority in (1, 2, 3):
        entities.append(
            SnowSensor(
                coordinator,
                f"priority_{priority}_streets",
                f"Priority {priority} Streets",
                lambda data, priority=priority: data["priority_counts"].get(str(priority), 0),
            )
        )

    for key, name in (("downtown", "Downtown"), ("a", "Zone A"), ("b", "Zone B")):
        entities.append(ZoneSensor(coordinator, key, name))

    async_add_entities(entities)


class BaseSnowSensor(CoordinatorEntity, SensorEntity):
    """Base class for sensors that track coordinator updates."""

    _attr_has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "idaho_falls")},
            name="Idaho Falls Snow Removal",
            manufacturer=MANUFACTURER,
            model="City snow GIS",
            configuration_url=coordinator.data["map_url"],
        )


class SnowSensor(BaseSnowSensor):
    """A sensor derived from normalized coordinator data."""

    def __init__(self, coordinator, key, name, value_fn):
        super().__init__(coordinator)
        self.value_fn = value_fn
        self._attr_name = name
        self._attr_unique_id = f"idaho_falls_snow_{key}"
        if "streets" in key or "segments" in key:
            self._attr_native_unit_of_measurement = "segments"
        elif "zones" in key:
            self._attr_native_unit_of_measurement = "zones"

    @property
    def native_value(self):
        """Return the current value from the latest coordinator data."""
        return self.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Expose source metadata for troubleshooting."""
        data = self.coordinator.data
        return {
            "source_url": data["source_url"],
            "map_url": data["map_url"],
            "city_page_updated": data["city_page"]["updated"],
            "city_parking_restrictions": data["city_page"]["parking_restrictions"],
            "source_data_updated": data["fetched_at"],
        }


class ZoneSensor(BaseSnowSensor):
    """A sensor showing the current status of one snow-removal zone."""

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"idaho_falls_snow_{key}"

    @property
    def native_value(self):
        """Return the current zone status."""
        return self.coordinator.data["zones"].get(self.key, {}).get("status", "unknown")

    @property
    def extra_state_attributes(self):
        """Expose zone details and source metadata."""
        data = self.coordinator.data
        return {
            **data["zones"].get(self.key, {}),
            "source_url": data["source_url"],
            "map_url": data["map_url"],
            "plow_method_counts": data["method_counts"],
            "plow_agency_counts": data["agency_counts"],
            "source_data_updated": data["fetched_at"],
        }
