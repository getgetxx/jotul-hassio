"""The 'JotulApi'."""

# class based on Jotul PF930
import asyncio
import json
import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import ATTR_DETAILED_STATUS_OPTIONS_MAPPING, QUERY_STRING_BASE, TIMEOUT

_LOGGER = logging.getLogger(__name__)

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
            queryStr = str.replace(QUERY_STRING_BASE, "(HOST)", self.host)+f"?cmd={self.op}"
            _LOGGER.debug("Start GetRequest : %s", queryStr)
            async with asyncio.timeout(TIMEOUT):
                # params = (("cmd", "GET ALLS"),)
                response = await session.get(queryStr)
                if(response.status != 200):
                    _LOGGER.error("Error during api request : http status returned is %s", response.status)
                    self.hass.states.async_set("jotulpelletcontrol.stove", "offline")
                    raise aiohttp.ClientError(f"Error during api request : http status returned is {response.status}")
                else :
                    resp_text = await response.text()
                    _LOGGER.debug("GetRequest response : %s", resp_text)
                    response_json = json.loads(resp_text)
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
        status = response_json["DATA"].get("STATUS")
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
        for key, value in self.response_json.items():
            if key == "STATUS":
                status = value  # Statut détaillé
                self.hass.states.async_set("jotulpelletcontrol.STATUS", ATTR_DETAILED_STATUS_OPTIONS_MAPPING.get(status, status))
            elif key == "F2L":
                self.hass.states.async_set("jotulpelletcontrol.F2L", int(value))  # Puissance ventilation max
            elif key == "PWR":
                self.hass.states.async_set("jotulpelletcontrol.PWR", value)  # Puissance
            elif key == "SETP":
                self.hass.states.async_set("jotulpelletcontrol.SETP", value)  # Température demandée
            elif key == "APLWDAY":
                self.hass.states.async_set("jotulpelletcontrol.APLWDAY", value)  # ????
            elif key == "F1RPM":
                self.hass.states.async_set("jotulpelletcontrol.F1RPM", value)  # RPM extracteur de fumée
            elif key == "FDR":
                self.hass.states.async_set("jotulpelletcontrol.FDR", value)  # ????
            elif key == "DPT":
                self.hass.states.async_set("jotulpelletcontrol.DPT", value)  # Deltra pressure target
            elif key == "DP":
                self.hass.states.async_set("jotulpelletcontrol.DP", value)  # Delta pressure
            elif key == "T1":
                self.hass.states.async_set("jotulpelletcontrol.T1", value)  # Température ambiante
            elif key == "T2":
                self.hass.states.async_set("jotulpelletcontrol.T2", value)  # Température pellet
            elif key == "T3":
                self.hass.states.async_set("jotulpelletcontrol.T3", value)  # Température des fumées
            elif key == "CHRSTATUS":
                self.hass.states.async_set("jotulpelletcontrol.CHRSTATUS", value)  # Statut d'activation de la programmation horaire
            elif key == "PQT":
                self.hass.states.async_set("jotulpelletcontrol.PQT", value)  # ????

    async def async_set_parameters(self, datas):
        """Set parameters following service call."""
        await self.async_set_setp(datas.get("SETP", None))  # temperature
        await self.async_set_powr(datas.get("PWR", None))  # fire power
        await self.async_set_rfan(datas.get("RFAN", None))  # Fan
        await self.async_set_status(datas.get("STATUS", None))  # status

    async def async_set_setp(self, value):
        """Set target temperature."""

        if value is None or not isinstance(value, int):
            return

        self.op = f"SET SETP {str(value)}"
        await self.async_get_request()

    async def async_set_powr(self, value):
        """Set power of fire."""
        if value is None:
            return

        self.op = f"SET POWR {str(value)}"
        await self.async_get_request()

    async def async_set_rfan(self, value):
        """Set fan level."""

        if value is None:
            return

        # must be str or int
        if not isinstance(value, str) and not isinstance(value, int):
            return

        self.op = f"SET RFAN {str(value)}"
        await self.async_get_request()

    async def async_set_chronostatus(self, value):
        """Enable or disable chrono program."""
        if value is None or not isinstance(value, int) or value not in (0, 1):
            _LOGGER.warning(
                "Trying to set chrono status with wrong value (must be int 0 or 1) : %s",
                value,
            )
            return

        self.op = f"SET CSST {str(value)}"
        _LOGGER.debug("Call GetRequest : %s", self.op)
        await self.async_get_request()

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
    except TimeoutError as err:
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
