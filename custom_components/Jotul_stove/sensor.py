"""Sensors for Jotul pellet control."""

import logging

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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

SENSOR_TYPES: list[SensorEntityDescription] = (
    SensorEntityDescription(
        key=ATTR_AMBIENT_TEMPERATURE,
        translation_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=ATTR_PELLET_TEMPERATURE,
        translation_key="pellet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=ATTR_SMOKE_TEMPERATURE,
        translation_key="smoke_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=ATTR_DETAILED_STATUS,
        translation_key="detailed_status",
        device_class=SensorDeviceClass.ENUM,
        state_class=SensorStateClass.MEASUREMENT,
        options=ATTR_DETAILED_STATUS_OPTIONS
    ),
    SensorEntityDescription(
        key=ATTR_TARGET_PRESSURE,
        translation_key="target_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_MEASURED_PRESSURE,
        translation_key="measured_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_SMOKE_FAN_SPEED,
        icon="mdi:fan-speed-2",
        translation_key="smoke_fan_speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=ATTR_UNIT_RPM,
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
    data = hass.data[DOMAIN].get(entry.entry_id)
    jotul_api = data.get("api")
    coordinator = data.get("coordinator")
    sensors = [ATTR_MEASURED_PRESSURE]
    sensors.append(ATTR_AMBIENT_TEMPERATURE)
    sensors.append(ATTR_PELLET_TEMPERATURE)
    sensors.append(ATTR_SMOKE_FAN_SPEED)
    sensors.append(ATTR_TARGET_PRESSURE)
    sensors.append(ATTR_DETAILED_STATUS)
    sensors.append(ATTR_SMOKE_TEMPERATURE)

    entities = [
        JotulSensor(coordinator, jotul_api, description)
        for description in SENSOR_TYPES
        if description.key in sensors
    ]
    async_add_entities(entities)

class JotulSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(self, coordinator, api, description: SensorEntityDescription) -> None:
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
        self._attr_native_value = self._api.response_json[ATTR_DICT_INF_SENSOR[self.entity_description.key].result_key_name]
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._attr_native_value
