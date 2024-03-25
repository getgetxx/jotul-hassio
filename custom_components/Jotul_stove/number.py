"""Numbers."""

import logging

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the number platform."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    jotul_api = data.get("api")
    async_add_entities([TargetTemperatureNumber(jotul_api, TARGET_TEMPERATURE_DESC)])

TARGET_TEMPERATURE_DESC = NumberEntityDescription(
        key="target_temperature",
        name = "Target temperature",
        icon="mdi:thermometer",
        native_max_value=25.0,
        native_min_value=15.0,
        mode=NumberMode.SLIDER,
        native_step=1.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE
    )

class TargetTemperatureNumber(NumberEntity):
    """Representation of temperature number."""

    def __init__(self, api, description)->None:
        """Initialize the number."""
        self.entity_description = description
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-target_temperature"
        self._attr_should_poll= True
        self._api = api

    async def async_update(self) -> None:
        """Get the latest state from the stove."""
        self._attr_native_value = self._api.response_json.get("SETP")

    async def async_set_native_value(self, value:float) -> None:
        """Set target temperature value."""
        await self._api.async_set_setp(int(value))
        self._attr_native_value = self._api.response_json.get("SETP")
        self.async_write_ha_state()
