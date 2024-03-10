"""Numbers."""

import asyncio
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, INTERVAL, TIMEOUT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant | None, entry, async_add_entities):
    """Set up the number platform."""
    jotul_api = hass.data[DOMAIN].get(entry.entry_id)
    coordinator = JotulNumbersUpdateCoordinator(hass, jotul_api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([TargetTemperatureNumber(coordinator, jotul_api)])

class JotulNumbersUpdateCoordinator(DataUpdateCoordinator):
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

class TargetTemperatureNumber(NumberEntity):
    """Representation of temperature number."""

    def __init__(self, coordinator, api)->None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._name = "Target temperature"
        self._friendly_name = "Température cible"
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-target_temperature"
        self._attr_has_entity_name = True
        self._attr_icon= "mdi:thermometer"
        # self._attr_should_poll= True
        self._api = api
        self._attr_max_value = 25
        self._attr_min_value= 15
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_max_value: 25
        self._attr_native_min_value: 15
        self._attr_native_step: 1
        self._attr_step = 1
        self._attr_device_class = NumberDeviceClass.TEMPERATURE
        # self._api.async_get_alls()


    @property
    def icon(self) -> str | None:
        """Icon of the entity."""
        return self._attr_icon

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._api.response_json["SETP"]

    async def async_set_native_value(self, value:float) -> None:
        """Set target temperature value."""
        await self._api.async_set_sept(value)
