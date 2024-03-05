"""Sensors for Jotul pellet control."""

import asyncio
from datetime import timedelta
import logging

from config.custom_components.jotul import JotulApi
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    ATTR_AMBIENT_TEMPERATURE,
    ATTR_DETAILED_STATUS,
    ATTR_DETAILED_STATUS_OPTIONS,
    ATTR_DICT_INF_SENSOR,
    ATTR_MEASURED_PRESSURE,
    ATTR_PELLET_TEMPERATURE,
    ATTR_SMOKE_FAN_SPEED,
    ATTR_SMOKE_TEMPERATURE,
    ATTR_TARGET_PRESSURE,
    ATTR_UNIT_RPM,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# @dataclass(frozen=True)
# class JotulRequiredKeysMixin:
#     """Mixin for required keys."""

#     infos: str
#     get_op: str
#     result_key:str

# class JotulEntityDescription(SensorEntityDescription, JotulRequiredKeysMixin):
#     """Describes Jotul sensor entity."""

SENSOR_TYPES: list[SensorEntityDescription] = (
    SensorEntityDescription(
        key=ATTR_AMBIENT_TEMPERATURE,
        translation_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        # infos="Température ambiante",
        # get_op="GET TMPS",
        # result_key="T1",
    ),
    SensorEntityDescription(
        key=ATTR_PELLET_TEMPERATURE,
        translation_key="pellet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        # infos="Température du pellet",
        # get_op="GET TMPS",
        # result_key="T2",
    ),
    SensorEntityDescription(
        key=ATTR_SMOKE_TEMPERATURE,
        translation_key="smoke_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        # infos="Température des fumées",
        # get_op="GET TMPS",
        # result_key="T3",
    ),
    SensorEntityDescription(
        key=ATTR_DETAILED_STATUS,
        translation_key="detailed_status",
        device_class=SensorDeviceClass.ENUM,
        state_class=SensorStateClass.MEASUREMENT,
        options=ATTR_DETAILED_STATUS_OPTIONS
        # infos="Température des fumées",
        # get_op="GET TMPS",
        # result_key="T3",
    ),
    # JotulEntityDescription(
    #     key=ATTR_CHRONO_STATUS,
    #     translation_key="chrono_status",
    #     device_class=SensorDeviceClass.ENUM,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     options=[ATTR_STATE_ON, ATTR_STATE_OFF],
    # ),
    # JotulEntityDescription(
    #     key=ATTR_TARGET_TEMPERATURE,
    #     translation_key="target_temperature",
    #     device_class=SensorDeviceClass.TEMPERATURE,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    #     infos="Température demandée",
    #     get_op="GET TMPS",
    #     result_key="",
    # ),
    SensorEntityDescription(
        key=ATTR_TARGET_PRESSURE,
        translation_key="target_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        # infos="Pression attendu",
        # get_op="GET DPRS",
        # result_key="DPT",
    ),
    SensorEntityDescription(
        key=ATTR_MEASURED_PRESSURE,
        translation_key="measured_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        # infos="Pression mesurée",
        # get_op="GET DPRS",
        # result_key="DP",
    ),
    SensorEntityDescription(
        key=ATTR_SMOKE_FAN_SPEED,
        icon="mdi:fan-speed-2",
        translation_key="smoke_fan_speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=ATTR_UNIT_RPM,
        # infos="Vitesse de ventilation des fumées",
        # get_op="GET FAND",
        # result_key="F1RPM",
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Old way of setting up the Jotul sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jotul based on config_entry."""
    jotul_api = hass.data[DOMAIN].get(entry.entry_id)
    coordinator = JotulCoordinator(hass, jotul_api)
    sensors = [ATTR_MEASURED_PRESSURE]
    sensors.append(ATTR_AMBIENT_TEMPERATURE)
    sensors.append(ATTR_PELLET_TEMPERATURE)
    sensors.append(ATTR_SMOKE_FAN_SPEED)
    sensors.append(ATTR_TARGET_PRESSURE)
    sensors.append(ATTR_DETAILED_STATUS)
    sensors.append(ATTR_SMOKE_TEMPERATURE)

    await coordinator.async_config_entry_first_refresh()

    entities = [
        JotulSensor(coordinator, jotul_api, description)
        for description in SENSOR_TYPES
        if description.key in sensors
    ]
    async_add_entities(entities)

class JotulCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant | None, my_api) -> None :
        """Initialize Jotul sensors coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Jotul sensors",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.my_api = my_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(10):
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

class JotulSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(self, coordinator: JotulCoordinator, api: JotulApi, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.mac}-{description.key}"
        self._attr_name = ATTR_DICT_INF_SENSOR[self.entity_description.key].label
        self._api = api

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[ATTR_DICT_INF_SENSOR[self.entity_description.key].result_key_name]
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._attr_native_value
