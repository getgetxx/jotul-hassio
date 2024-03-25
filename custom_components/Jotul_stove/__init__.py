"""The "jotulpelletcontrol" custom component.

This component permit to connect to Jotul module and control it
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import JotulCoordinator
from .jotul_api import jotul_api_setup

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:  # noqa: D103
    _LOGGER.info(
        "Initializing %s integration with plaforms: %s with config: %s",
        DOMAIN,
        PLATFORMS,
        config,
    )

    api = await jotul_api_setup(hass, config.data.get(CONF_HOST, None))
    coordinator = JotulCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    # services
    def set_parameters(call):
        """Handle the service call 'set'."""
        api.async_set_parameters(call.data)

    def set_targettemp(call):
        """Handle the service call 'Set target temperature'."""
        api.async_set_setp(call.data.get("value", None))

    def set_maxfan(call):
        """Handle the service call 'Set the max fan pwr'."""
        api.async_set_rfan(call.data.get("value", None))

    def set_status(call):
        """Handle the service call 'Set status on or off'."""
        api.async_set_status(call.data.get("value", None))

    def set_power(call):
        """Handle the service call 'Set Power 1 to 5'."""
        api.async_set_powr(call.data.get("value", None))

    def get_alls(call):
        """Handle the service call 'Get all data'."""
        api.async_get_alls()

    def get_allcounters(calle):
        """Hande the service call 'Get all counter'."""
        api.async_get_cntr()

    def set_silentmode(call):
        """Handle the servie call 'Set silent mode value'."""
        api.async_set_silentmode(call.data.get("value", None))

    def set_chronostatus(call):
        """Handle the service call 'set chrono status'."""
        api.async_set_chronostatus(call.data.get("value", None))

    hass.services.async_register(DOMAIN, "set_parms", set_parameters)
    hass.services.async_register(DOMAIN, "set_targettemp", set_targettemp)
    hass.services.async_register(DOMAIN, "set_maxfan", set_maxfan)
    hass.services.async_register(DOMAIN, "set_status", set_status)
    hass.services.async_register(DOMAIN, "set_power", set_power)
    hass.services.async_register(DOMAIN, "get_alls", get_alls)
    hass.services.async_register(DOMAIN, "get_allcounters", get_allcounters)
    hass.services.async_register(DOMAIN, "set_silentmode", set_silentmode)
    hass.services.async_register(DOMAIN, "set_chronostatus", set_chronostatus)

    hass.data.setdefault(DOMAIN, {}).update({config.entry_id: {"api": api, "coordinator":coordinator}})
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

    # Return boolean to indicate that initialization was successfully.
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok
