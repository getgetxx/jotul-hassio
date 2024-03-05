"""Switch."""

import asyncio
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the switch platform."""
    jotul_api = hass.data[DOMAIN].get(entry.entry_id)
    coordinator = JotulSwitchUpdateCoordinator(hass, jotul_api)
    await coordinator.async_config_entry_first_refresh()

    await async_add_entities([StatusSwitch(coordinator, jotul_api), ChronoStatusSwitch(coordinator, jotul_api)])

class JotulSwitchUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching switch data."""

    def __init__(self, hass: HomeAssistant|None, jotul_api) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.data = None
        self.my_api = jotul_api

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),  # Update interval
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with asyncio.timeout(10):
                await self.my_api.async_get_alls()
        except BaseException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

class StatusSwitch(ToggleEntity):
    """Representation of status Switch."""

    def __init__(self, coordinator, api)->None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._name = "Etat"
        self._friendly_name = "Etat"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-status"
        self._attr_has_entity_name = True
        self._attr_icon= "mdi:fireplace"
        self._attr_should_poll= True
        self._api = api

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return bool(self._api.response_json.get(self._name))
        # return bool(self.coordinator.data and self.coordinator.data.get(self._name))

    async def async_turn_on(self, **kwargs):
        """Turn the stove on."""
        await self._api.async_set_status(True)

    async def async_turn_off(self, **kwargs):
        """Turn the stove off."""
        await self.api.async_set_status(False)


class ChronoStatusSwitch(ToggleEntity):
    """Representation of chrono status switch."""

    def __init__(self, coordinator, api)->None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._name = "Etat"
        self._friendly_name = "Etat"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-status"
        self._attr_has_entity_name = True
        self._attr_icon= "mdi:fireplace"
        self._attr_should_poll= True
        self._api = api

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return True if self._api.response_json.get("CHRSTATUS") == 1 else False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._api.async_set_chronostatus(1)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._api.async_set_chronostatus(0)

    async def async_toggle(self, **kwargs: logging.Any) -> None:
        """Toogle the switch."""
        await self._api.async_set_chronostatus(0 if self.is_on else 1)
