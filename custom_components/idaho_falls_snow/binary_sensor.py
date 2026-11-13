"""Binary sensor for Idaho Falls snow-removal activity."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the snow-event binary sensor."""
    async_add_entities([SnowEvent(entry.runtime_data)])


class SnowEvent(CoordinatorEntity, BinarySensorEntity):
    """Represent whether snow-removal operations are active."""

    _attr_has_entity_name = True
    _attr_name = "Snow Event"
    _attr_unique_id = "idaho_falls_snow_event"
    _attr_icon = "mdi:snowflake-alert"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "idaho_falls")},
            name="Idaho Falls Snow Removal",
            manufacturer=MANUFACTURER,
            model="City snow GIS",
            configuration_url=coordinator.data["map_url"],
        )

    @property
    def is_on(self):
        """Return whether snow-removal activity is currently active."""
        return self.coordinator.data["active"]

    @property
    def extra_state_attributes(self):
        """Expose activity details and source metadata."""
        data = self.coordinator.data
        return {
            key: data[key]
            for key in (
                "working_streets",
                "completed_streets",
                "working_zones",
                "completed_zones",
            )
        } | {
            "city_page_updated": data["city_page"]["updated"],
            "city_parking_restrictions": data["city_page"]["parking_restrictions"],
            "source_url": data["source_url"],
            "map_url": data["map_url"],
            "source_data_updated": data["fetched_at"],
        }
