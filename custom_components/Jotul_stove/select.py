"""Numbers."""

import asyncio
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_FAN_LEVEL_MAPING_REVERSE,
    ATTR_FAN_LEVEL_MAPPING,
    DOMAIN,
    INTERVAL,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the number platform."""
    jotul_api = hass.data[DOMAIN].get(entry.entry_id)
    coordinator = JotulEnumUpdateCoordinator(hass, jotul_api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([VentilationModeSelect(coordinator, jotul_api)])

class JotulEnumUpdateCoordinator(DataUpdateCoordinator):
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
            update_interval=INTERVAL,  # Update interval
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with asyncio.timeout(TIMEOUT):
                await self.my_api.async_get_alls()
        except BaseException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

class VentilationModeSelect(SelectEntity):
    """Representation of temperature number."""

    def __init__(self, coordinator, api)->None:
        """Initialize the switch."""
        self.coordinator = coordinator
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

    # async def async_set_current_option(self, value:float) -> None:
    #     """Set target temperature value."""
    #     await self._api.async_set_rfan(ATTR_FAN_LEVEL_MAPING_REVERSE[value])

    # async def async_get_native_value(self) -> float:
    #     """Turn the stove off."""
    #     return self._api.response_json["T1"]
