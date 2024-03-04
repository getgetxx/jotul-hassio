# from config.custom_components.jotul import JotulApi
# from homeassistant.components.switch import SwitchEntity


# class JotulOnOffSwitch(SwitchEntity):
#     """On off Jotul state"""

#     _attr_icon= "mdi:fireplace"
#     _attr_should_poll= True
#     _attr_name = "Etat"
#     _attr_has_entity_name = True


#     def __init__(self, api: JotulApi) -> None:
#         """Initialize Jotul on off switch."""
#         self._api = api
#         self._attr_device_info = api.device_info
#         self._attr_unique_id = f"{api.device.mac}-streamer"
import logging

import async_timeout
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    coordinator = JotulSwitchUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([CustomSwitch(coordinator, "state", "State Switch"), CustomSwitch(coordinator, "chrono", "Chrono Switch")])

class JotulSwitchUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching switch data."""

    def __init__(self, hass):
        """Initialize the coordinator."""
        self.hass = hass
        self.data = None

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),  # Update interval
        )

    async def _async_update_data(self):
        """Fetch data from API."""

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # listening_idx = set(self.async_contexts())
                return await self.my_api.async_get_alls()
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        except BaseException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

class CustomSwitch(ToggleEntity):
    """Representation of a Switch."""

    def __init__(self, coordinator, name, friendly_name)->None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._name = name
        self._friendly_name = friendly_name

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return bool(self.coordinator.data and self.coordinator.data.get(self._name))

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        # Turn on logic here
        pass

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        # Turn off logic here
        pass

    @property
    def friendly_name(self):
        """Return the friendly name of the switch."""
        return self._friendly_name
