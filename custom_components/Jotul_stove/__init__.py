"""The "jotulpelletcontrol" custom component.

This component permit to connect to Jotul module and control it
"""

import asyncio
from datetime import timedelta
import json
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    ATTR_DETAILED_STATUS_OPTIONS_MAPPING,
    DOMAIN,
    PLATFORMS,
    QUERY_STRING_BASE,
    TIMEOUT,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:  # noqa: D103
    _LOGGER.info(
        "Initializing %s integration with plaforms: %s with config: %s",
        DOMAIN,
        PLATFORMS,
        config,
    )

    api = await jotul_api_setup(hass, config.data.get(CONF_HOST, None))

    # services
    def set_parameters(call):
        """Handle the service call 'set'."""
        api.async_set_parameters(call.data)

    def set_targettemp(call):
        """Handle the service call 'Set target temperature'."""
        api.async_set_sept(call.data.get("value", None))

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

    hass.data.setdefault(DOMAIN, {}).update({config.entry_id: api})
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


# class based on NINA 6kw
# contact me if you have a other model of stove
class JotulApi:
    """API JOTUL."""

    op = None
    response_json = None

    def __init__(self, mac, sn, host:str, hass:HomeAssistant) -> None:  # noqa: D107

        self.hass = hass
        self.mac = mac
        self.sn = sn
        self.host = host
        self.queryStr = str.replace(QUERY_STRING_BASE, "(HOST)", host)
        self._available = True
        _LOGGER.debug("Init of class jotulpelletcontrol")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
                    connections={("ip", self.host), ("mac", self.mac)},
                    # manufacturer="Jotul",
                    manufacturer="Jotul",
                    model= "PF930",
                    name="JOTUL PF930",
                    # model="PF930",
                    serial_number=self.sn
        )

    # make request GET ALLS
    async def async_get_alls(self):
        """Get All data or almost ;)."""
        self.op = "GET ALLS"
        return await self.async_get_request()

    # make request GET CNTR
    async def async_get_cntr(self):
        """Get counters."""
        self.op = "GET CNTR"
        await self.async_get_request()

    async def get_sensor_value(self, op):
        """Get some value."""
        self.op = op
        return await self.async_get_request()

    # send a get request for get datas
    async def async_get_request(self) -> None:
        """Request the stove."""
        # params for GET
        # params = (("cmd", self.op),)

        # check if op is defined or stop here
        if self.op is None:
            raise ValueError("self.op")

        # let's go baby
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(TIMEOUT):
                # params = (("cmd", "GET ALLS"),)
                response = await session.get(str.replace(QUERY_STRING_BASE, "(HOST)", self.host)+"?cmd=GET+ALLS")
                if(response.status != 200):
                    _LOGGER.error("Error during api request : http status returned is %s", response.status)
                    self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
                    raise aiohttp.ClientError(f"Error during api request : http status returned is {response.status}")
                else :
                    response_json = json.loads(await response.text())
        except aiohttp.ClientError as client_error:
            _LOGGER.error("Error during api request: {emsg}".format(emsg=client_error))  # noqa: UP032, G001
            self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
            raise
        except json.decoder.JSONDecodeError:
            _LOGGER.error("Error during json parsing: response unexpected from Cbox")
            self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
            raise

        # If no response return
        if response_json["SUCCESS"] is not True:
            self.hass.states.async_set(
                "jotulpelletcontrol.stove", "com error", self.response_json
            )
            _LOGGER.error("Error returned by CBox")
            raise aiohttp.ClientResponseError(response)

        # mapping du status int to text
        status = response_json["DATA"]["STATUS"]
        if status is not None :
            response_json["DATA"]["STATUS_TXT"] = ATTR_DETAILED_STATUS_OPTIONS_MAPPING[status]
            response_json["DATA"]["Etat"] = 1 if (status > 1 and status < 10) or status == 11 else 0

        # merge response with existing dict
        if self.response_json is not None:
            response_merged = self.response_json.copy()
            response_merged.update(response_json["DATA"])
            self.response_json = response_merged
        else:
            self.response_json = response_json["DATA"]

        self.hass.states.async_set(
            "jotulpelletcontrol.stove", "online", self.response_json
        )
        await self.change_states()
        # return self.response_json

    async def change_states(self):
        """Change states following result of request."""
        # if self.op == "GET ALLS":
        self.hass.states.async_set("jotulpelletcontrol.STATUS", ATTR_DETAILED_STATUS_OPTIONS_MAPPING.get(
            self.response_json["STATUS"], self.response_json["STATUS"])) # Statut détaillé
        self.hass.states.async_set("jotulpelletcontrol.F2L", int(self.response_json["F2L"])) # Puissance ventilation max
        self.hass.states.async_set("jotulpelletcontrol.PWR", self.response_json["PWR"]) # Puissance
        self.hass.states.async_set("jotulpelletcontrol.SETP", self.response_json["SETP"]) # Température demandé
        self.hass.states.async_set("jotulpelletcontrol.APLWDAY", self.response_json["APLWDAY"]) # ????
        self.hass.states.async_set("jotulpelletcontrol.F1RPM", self.response_json["F1RPM"]) # RPM extracteur de fumée
        self.hass.states.async_set("jotulpelletcontrol.FDR", self.response_json["FDR"]) # ????
        self.hass.states.async_set("jotulpelletcontrol.DPT", self.response_json["DPT"]) # Deltra pressure target
        self.hass.states.async_set("jotulpelletcontrol.DP", self.response_json["DP"]) # Delta pressure
        self.hass.states.async_set("jotulpelletcontrol.T1", self.response_json["T1"]) # Température ambiante
        self.hass.states.async_set("jotulpelletcontrol.T2", self.response_json["T2"]) # Température pellet
        self.hass.states.async_set("jotulpelletcontrol.T3", self.response_json["T3"]) # Température des fumées
        self.hass.states.async_set("jotulpelletcontrol.CHRSTATUS", self.response_json["CHRSTATUS"]) # Satus d'activation de la programmation horaire
        self.hass.states.async_set("jotulpelletcontrol.PQT", self.response_json["PQT"]) # ????


    async def async_set_parameters(self, datas):
        """Set parameters following service call."""
        await self.async_set_sept(datas.get("SETP", None))  # temperature
        await self.async_set_powr(datas.get("PWR", None))  # fire power
        await self.async_set_rfan(datas.get("RFAN", None))  # Fan
        await self.async_set_status(datas.get("STATUS", None))  # status

    async def async_set_sept(self, value):
        """Set target temperature."""

        if value is None or not isinstance(value, int):
            return

        self.op = f"SET SETP {str(value)}"
        await self.async_get_request()
        # change state
        await self.hass.states.set("jotulpelletcontrol.SETP", self.response_json["SETP"])

    async def async_set_powr(self, value):
        """Set power of fire."""
        if value is None:
            return

        self.op = f"SET POWR {str(value)}"
        await self.async_get_request()

        # change state
        await self.hass.states.set("jotulpelletcontrol.PWR", self.response_json["PWR"])

    async def async_set_rfan(self, value):
        """Set fan level."""

        if value is None:
            return

        # must be str or int
        if not isinstance(value, str) and not isinstance(value, int):
            return

        self.op = f"SET RFAN {str(value)}"
        await self.async_get_request()

        # change state
        self.hass.states.async_set("jotulpelletcontrol.F2L", self.response_json["F2L"])

    async def async_set_chronostatus(self, value):
        """Enable or disable chrono program."""
        if value is None or not isinstance(value, int) or value not in (0, 1):
            _LOGGER.warning(
                "Trying to set chrono status with wrong value (must be int 0 or 1) : %s",
                value,
            )
            return

        self.op = f"SET CSST {str(value)}"
        await self.async_get_request()

        # change state
        self.hass.states.async_set(
            "jotulpelletcontrol.CHRSTATUS", self.response_json["CHRSTATUS"]
        )

    async def async_set_status(self, value):
        """Set the state on or off of the stove."""
        _LOGGER.debug("set_status -- start or stop stove => %s", value)
        if value is None:
            return

        _LOGGER.debug("set_status -- Vérification du type de la valeur (str) passé!")

        if value not in ("on", "off", True, False):
            return

        _LOGGER.debug("set_status -- Vérification on, off, True or False value passé!")

        if isinstance(value, bool):
            if value is True:
                value = "ON"
            else:
                value = "OFF"

        self.op = f"CMD {str(value).upper()}"
        await self.async_get_request()

        # change state
        self.hass.states.async_set(
            "jotulpelletcontrol.STATUS",
            ATTR_DETAILED_STATUS_OPTIONS_MAPPING.get(
                self.response_json["STATUS"], self.response_json["STATUS"]
            ),
        )

    async def async_set_silentmode(self, value):
        """Set silent mode 0 or 1 (off/on)."""

        if value is None:
            return

        # must be int
        if not isinstance(value, int):
            _LOGGER.warning(
                "Set silent mode with unauthorized value (not a int) %s", value
            )
            return

        self.op = f"SLNT {str(value)}"
        await self.async_get_request()

        # change state
        self.hass.states.async_set("jotulpelletcontrol.f2l", self.response_json["F2L"])

    def get_datas(self):  # noqa: D102
        return self.response_json


async def jotul_api_setup(
    hass: HomeAssistant,
    host: str,
) -> JotulApi | None :
    """Create a Jotul instance only once."""

    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(TIMEOUT):
            # params = (("cmd", "GET ALLS"),)
            resp = await session.get(str.replace(QUERY_STRING_BASE, "(HOST)", host)+"?cmd=GET+ALLS")
            if(resp.status == 200):
                jsonR = await resp.json(content_type=resp.content_type)
                mac = jsonR["DATA"]["MAC"]
                sn = jsonR["DATA"]["SN"]
            else :
                _LOGGER.debug("response not ok : %s", resp)
                raise ConfigEntryNotReady("First get request do not reply 200")
    except asyncio.TimeoutError as err:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady from err
    except aiohttp.ClientConnectionError as err:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady from err
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        raise ConfigEntryNotReady from err

    api = JotulApi(mac, sn, host, hass)

    return api
