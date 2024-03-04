"""The "jotulpelletcontrol" custom component.

This component permit to connect to Jotul module and control it
"""

import asyncio
from datetime import timedelta
import json
import logging
import time
from typing import Any

import aiohttp
import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import Throttle

from .const import ATTR_DETAILED_STATUS_OPTIONS_MAPPING, DOMAIN, INTERVAL, INTERVAL_CNTR, PLATFORMS, QUERY_STRING_BASE, TIMEOUT

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
    # await api.async_get_alls()
    # await api.async_get_cntr()

    # loop for get state of stove

    # def update_state_datas(event_time):
    #     return asyncio.run_coroutine_threadsafe(api.async_get_alls(), hass.loop)

    # loop for get counter of stove
    # def update_cntr_datas(event_time):
    #     return asyncio.run_coroutine_threadsafe(api.async_get_cntr(), hass.loop)

    # async_track_time_interval(hass, update_state_datas, INTERVAL)
    # async_track_time_interval(hass, update_cntr_datas, INTERVAL_CNTR)

    # services
    def set_parameters(call):
        """Handle the service call 'set'."""
        api.set_parameters(call.data)

    def set_targettemp(call):
        """Handle the service call 'Set target temperature'."""
        api.set_sept(call.data.get("value", None))

    def set_maxfan(call):
        """Handle the service call 'Set the max fan pwr'."""
        api.set_rfan(call.data.get("value", None))

    def set_status(call):
        """Handle the service call 'Set status on or off'."""
        api.set_status(call.data.get("value", None))

    def set_power(call):
        """Handle the service call 'Set Power 1 to 5'."""
        api.set_powr(call.data.get("value", None))

    def get_alls(call):
        """Handle the service call 'Get all data'."""
        params = (("cmd", "GET ALLS"),)
        api.request_stove("GET ALLS", params)
        api.change_states()

    def get_allcounters(calle):
        """Hande the service call 'Get all counter'."""
        api.async_get_cntr()

    def set_silentmode(call):
        """Handle the servie call 'Set silent mode value'."""
        api.set_silentmode(call.data.get("value", None))

    def set_chronostatus(call):
        """Handle the service call 'set chrono status'."""
        api.set_chronostatus(call.data.get("value", None))

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

    pinged = False
    op = None
    response_json = None

    last_op = None
    last_params = None

    """docstring for jotulpelletcontrol"""

    def __init__(self, mac, sn, host:str, hass:HomeAssistant) -> None:  # noqa: D107

        self.hass = hass
        # self.device_info = DeviceInfo(**devInfos)
        self.mac = mac
        self.sn = sn
        self.host = host
        self.queryStr = str.replace(QUERY_STRING_BASE, "(HOST)", host)
        self._available = True
        # "http://" + self.host + "/cgi-bin/sendmsg.lua"

        _LOGGER.debug("Init of class jotulpelletcontrol")

        self.code_fan_nina = {0: "off", 6: "high", 7: "auto"}
        self.code_fan_nina_reversed = {"off": 0, "high": 6, "auto": 7}

        # self.async_get_alls()

        # States are in the format DOMAIN.OBJECT_ID.
        # hass.states.async_set('jotulpelletcontrol.host', self.host)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs: Any) -> None:
        """Pull the latest data from Jotul."""
        try:
            await self.device.update_status()
            self._available = True
        except aiohttp.ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.ip_address)
            self._available = False

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
    async def async_get_request(self):
        """Request the stove."""
        # params for GET
        params = (("cmd", self.op),)

        # check if op is defined or stop here
        if self.op is None:
            raise ValueError("self.op")

        # let's go baby
        try:
            async with aiohttp.ClientSession() as session, session.get(
                self.queryStr, params=params
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Error during api request : http status returned is {}".format(
                            response.status
                        )
                    )  # noqa: UP032, G001
                    self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
                    raise aiohttp.ClientError(
                        "Error during api request : http status returned is {}".format(
                            response.status
                        ))
                    # response = False
                else:
                    # save response in json object
                    response_json = json.loads(await response.text())

        except aiohttp.ClientError as client_error:
            _LOGGER.error("Error during api request: {emsg}".format(emsg=client_error))  # noqa: UP032, G001
            self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
            # response = False
            raise
        except json.decoder.JSONDecodeError:
            _LOGGER.error("Error during json parsing: response unexpected from Cbox")
            self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
            # response = False
            raise

        # if response is False:
            # _LOGGER.debug("get_request() response false for op " + self.op)  # noqa: G003
            # return False

        # If no response return
        if response_json["SUCCESS"] is not True:
            self.hass.states.async_set(
                "jotulpelletcontrol.stove", "com error", self.response_json
            )
            _LOGGER.error("Error returned by CBox")
            raise aiohttp.ClientResponseError(response)

        # merge response with existing dict
        if self.response_json is not None:
            response_merged = self.response_json.copy()
            response_merged.update(response_json["DATA"])
            self.response_json = response_merged
        else:
            self.response_json = response_json["DATA"]
            # mapping du status int to text
            self.response_json["STATUS_TXT"] = ATTR_DETAILED_STATUS_OPTIONS_MAPPING[self.response_json["STATUS"]]

        self.hass.states.async_set(
            "jotulpelletcontrol.stove", "online", self.response_json
        )
        # self.change_states()
        return self.response_json

    # send request to stove
    def request_stove(self, op, params):  # noqa: D102
        _LOGGER.debug("request stove " + op)  # noqa: G003
        _LOGGER.debug("request stove params" + str(params))  # noqa: G003

        if op is None:
            return False

        # save
        self.last_op = op
        self.last_params = str(params)

        retry = 0
        success = False
        response = ""
        # error returned by Cbox
        while not success:
            # let's go baby
            try:
                response = requests.get(self.queryStr, params=params, timeout=30)
            except requests.exceptions.ReadTimeout:
                # timeout ( can happend when wifi is used )
                _LOGGER.error("Timeout reach for request : %s", self.queryStr)
                _LOGGER.info("Please check if you can ping : %s", self.host)
                self.hass.states.set("jotulpelletcontrol.stove", "offline")
                return False
            except requests.exceptions.ConnectTimeout:
                # equivalent of ping
                _LOGGER.error("Please check parm host : %s", self.host)
                self.hass.states.set("jotulpelletcontrol.stove", "offline")
                return False

            if response is False:
                return False

            _LOGGER.debug("request url: %s", response.url)
            _LOGGER.debug("response to request (%s) : %s", op, response.text)
            # save response in json object
            response_json = json.loads(response.text)
            success = response_json["SUCCESS"]

            # cbox return error
            if not success:
                self.hass.states.async_set(
                    "jotulpelletcontrol.stove", "com error", self.response_json
                )
                _LOGGER.error("Error returned by CBox - retry in 2 seconds (%s)", op)
                time.sleep(2)
                retry = retry + 1

                if retry == 3:
                    _LOGGER.error(
                        "Error returned by CBox - stop retry after 3 attempt (%s)", op
                    )
                    break

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

        return response

    def change_states(self):
        """Change states following result of request."""
        if self.op == "GET ALLS":
            self.hass.states.async_set(
                "jotulpelletcontrol.STATUS",
                self.code_status.get(
                    self.response_json["STATUS"], self.response_json["STATUS"]
                ),
            )
            self.hass.states.async_set(
                "jotulpelletcontrol.F2L", int(self.response_json["F2L"])
            )  # Puissance ventilation max
            self.hass.states.async_set(
                "jotulpelletcontrol.PWR", self.response_json["PWR"]
            )  # Puissance
            self.hass.states.async_set(
                "jotulpelletcontrol.SETP", self.response_json["SETP"]
            )  # Température demandé
            self.hass.states.async_set(
                "jotulpelletcontrol.APLWDAY", self.response_json["APLWDAY"]
            )  # ????
            # RPM extracteur de fumée
            self.hass.states.async_set(
                "jotulpelletcontrol.F1RPM", self.response_json["F1RPM"]
            )
            self.hass.states.async_set(
                "jotulpelletcontrol.FDR", self.response_json["FDR"]
            )  # ????
            # Deltra pressure target
            self.hass.states.async_set(
                "jotulpelletcontrol.DPT", self.response_json["DPT"]
            )
            self.hass.states.async_set(
                "jotulpelletcontrol.DP", self.response_json["DP"]
            )  # Delta pressure
            self.hass.states.async_set(
                "jotulpelletcontrol.T1", self.response_json["T1"]
            )  # Température ambiante
            self.hass.states.async_set(
                "jotulpelletcontrol.T2", self.response_json["T2"]
            )  # Température pellet
            # Température des fumées
            self.hass.states.async_set(
                "jotulpelletcontrol.T3", self.response_json["T3"]
            )
            # Satus d'activation de la programmation horaire
            self.hass.states.async_set(
                "jotulpelletcontrol.CHRSTATUS", self.response_json["CHRSTATUS"]
            )
            self.hass.states.async_set(
                "jotulpelletcontrol.PQT", self.response_json["PQT"]
            )  # ????

    def get_sept(self):
        """Get target temperature for climate."""
        if self.response_json is None or self.response_json["SETP"] is None:
            return 0

        return self.response_json["SETP"]

    def set_parameters(self, datas):
        """Set parameters following service call."""
        self.set_sept(datas.get("SETP", None))  # temperature
        self.set_powr(datas.get("PWR", None))  # fire power
        self.set_rfan(datas.get("RFAN", None))  # Fan
        self.set_status(datas.get("STATUS", None))  # status

    def set_sept(self, value):
        """Set target temperature."""

        if value is None or value.isinstance(int):
            return

        op = "SET SETP"

        # params for GET
        params = (("cmd", op + " " + str(value)),)

        # avoid multhostle request
        if op == self.last_op and str(params) == self.last_params:
            _LOGGER.debug("retry for op :%s avoided", op)
            return

        # request the stove
        if self.request_stove(op, params) is False:
            return

        # change state
        self.hass.states.set("jotulpelletcontrol.SETP", self.response_json["SETP"])

    def set_powr(self, value):
        """Set power of fire."""
        if value is None:
            return

        op = "SET POWR"

        # params for GET
        params = (("cmd", op + " " + str(value)),)

        # avoid multhostle request
        if op == self.last_op and str(params) == self.last_params:
            _LOGGER.debug("retry for op :%s avoided", op)
            return

        # request the stove
        if self.request_stove(op, params) is False:
            return

        # change state
        self.hass.states.set("jotulpelletcontrol.PWR", self.response_json["PWR"])

    def set_rfan(self, value):
        """Set fan level."""

        if value is None:
            return

        # must be str or int
        if not value.isinstance(str) and not value.isinstance(int):
            return

        op = "SET RFAN"

        # params for GET
        params = (("cmd", op + " " + str(value)),)

        # avoid multhostle request
        if op == self.last_op and str(params) == self.last_params:
            _LOGGER.debug("retry for op :%s avoided", op)
            return

        # request the stove
        if self.request_stove(op, params) is False:
            return

        # change state
        self.hass.states.async_set("jotulpelletcontrol.F2L", self.response_json["F2L"])

    def set_chronostatus(self, value):
        """Enable or disable chrono program."""
        if value is None or not value.isinstance(int) or value not in (0, 1):
            _LOGGER.warning(
                "Trying to set chrono status with wrong value (must be int 0 or 1) : %s",
                value,
            )
            return

        op = "SET CSST"
        params = (("cmd", op + " " + str(value)),)

        # avoid multhostle request
        if op == self.last_op and str(params) == self.last_params:
            _LOGGER.debug("retry for op :%s avoided", op)
            return

        # request the stove
        if self.request_stove(op, params) is False:
            return

        # change state
        self.hass.states.async_set(
            "jotulpelletcontrol.CHRSTATUS", self.response_json["CHRSTATUS"]
        )

    def set_status(self, value):  # noqa: D102
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

        op = "CMD"

        # params for GET
        params = (("cmd", op + " " + str(value).upper()),)

        # request the stove
        if self.request_stove(op, params) is False:
            return

        # change state
        self.hass.states.async_set(
            "jotulpelletcontrol.STATUS",
            self.code_status.get(
                self.response_json["STATUS"], self.response_json["STATUS"]
            ),
        )

    def set_silentmode(self, value):
        """Set silent mode 0 or 1 (off/on)."""

        if value is None:
            return

        # must be int
        if not value.isinstance(int):
            _LOGGER.warning(
                "Set silent mode with unauthorized value (not a int) %s", value
            )
            return

        op = "SET SLNT"

        # params for GET
        params = (("cmd", op + " " + str(value)),)

        # avoid multhostle request
        if op == self.last_op and str(params) == self.last_params:
            _LOGGER.debug("retry for op :%s avoided", op)
            return

        # request the stove
        if self.request_stove(op, params) is False:
            return

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
                # device = DeviceInfo(
                #     connections={("ip", host), ("mac", jsonR["DATA"]["MAC"])},
                #     # manufacturer="Jotul",
                #     default_manufacturer="Jotul",
                #     default_model= "PF930",
                #     default_name="JOTUL PF930",
                #     # model="PF930",
                #     deviceMac = jsonR["DATA"]["MAC"],
                #     serial_number=jsonR["DATA"]["SN"]
                # )
            else :
                _LOGGER.debug("response not ok", resp)
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
        # return None

    api = JotulApi(mac, sn, host, hass)

    return api
