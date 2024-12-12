"""Numbers."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant

from .const import ATTR_FAN_LEVEL_MAPING_REVERSE, ATTR_FAN_LEVEL_MAPPING, ATTR_MAX_POWER_MAPING_REVERSE, ATTR_MAX_POWER_MAPPING, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the number platform."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    jotul_api = data.get("api")

    async_add_entities([VentilationModeSelect(jotul_api), MaxPowerSelect(jotul_api)])

class VentilationModeSelect(SelectEntity):
    """Representation of temperature number."""

    def __init__(self, api)->None:
        """Initialize the select."""
        self._name = "Ventilation"
        self._friendly_name = "Mode de ventilation"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-ventilation_mode"
        self._attr_has_entity_name = True
        self._attr_icon= "mdi:fan"
        self._attr_should_poll= True
        self._api = api
        self._attr_options = ["Off", "1", "2", "3", "4", "5", "Max", "Auto"]

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return self._attr_icon

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def current_option(self) -> float | None:
        """Return the state of the sensor."""
        return ATTR_FAN_LEVEL_MAPPING[self._api.response_json["F2L"]]

    async def async_select_option(self, option:str) -> None:
        """Set target Ventilation mode."""
        await self._api.async_set_rfan(ATTR_FAN_LEVEL_MAPING_REVERSE[option])


class MaxPowerSelect(SelectEntity):
    """Representation of max power number."""

    def __init__(self, api)->None:
        """Initialize the selct."""
        self._name = "Puissance"
        self._friendly_name = "Puissance maximum"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-max_power"
        self._attr_has_entity_name = True
        self._attr_icon= "mdi:fire"
        self._attr_should_poll= True
        self._api = api
        self._attr_options = ["1", "2", "3", "4", "5"]

    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return self._attr_icon

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def current_option(self) -> float | None:
        """Return the state of the sensor."""
        return ATTR_MAX_POWER_MAPPING[self._api.response_json["PWR"]]

    async def async_select_option(self, option:str) -> None:
        """Set target Ventilation mode."""
        await self._api.async_set_powr(ATTR_MAX_POWER_MAPING_REVERSE[option])
