"""Switch."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the switch platform."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    jotul_api = data.get("api")

    async_add_entities([StatusSwitch(jotul_api), ChronoStatusSwitch(jotul_api)])

class StatusSwitch(ToggleEntity):
    """Representation of status Switch."""

    def __init__(self, api)->None:
        """Initialize the switch."""
        self._name = "Etat"
        self._friendly_name = "Etat"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-status"
        self._attr_has_entity_name = True
        self._attr_should_poll= True
        self._api = api

    @property
    def icon(self) -> str | None:
        """Icon of the entity based on value."""
        if self.is_on:
            return "mdi:fireplace"
        else:
            return "mdi:fireplace-off"

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return bool(self._api.response_json.get(self._name))

    async def async_turn_on(self, **kwargs):
        """Turn the stove on."""
        await self._api.async_set_status(True)

    async def async_turn_off(self, **kwargs):
        """Turn the stove off."""
        await self.api.async_set_status(False)

    async def async_toggle(self, **kwargs) -> None:
        """Toogle the switch."""
        await self._api.async_set_status(not self.is_on)


class ChronoStatusSwitch(ToggleEntity):
    """Representation of chrono status switch."""

    def __init__(self, api)->None:
        """Initialize the switch."""
        self._name = "Chrono"
        self._friendly_name = "Mode programmation"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-chronostatus"
        self._attr_has_entity_name = True
        self._attr_should_poll= True
        self._api = api

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def icon(self) -> str | None:
        """Icon of the entity based on value."""
        if self.is_on:
            return "mdi:clock-check"
        else:
            return "mdi:clock-remove"
    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._api.response_json.get("CHRSTATUS") == 1

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._api.async_set_chronostatus(1)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._api.async_set_chronostatus(0)

    async def async_toggle(self, **kwargs) -> None:
        """Toogle the switch."""
        await self._api.async_set_chronostatus(0 if self.is_on else 1)
