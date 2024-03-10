"""Constants for Jotul."""
# The domain of your component. Should be equal to the name of your component.  # noqa: D100
from datetime import timedelta

from homeassistant.const import Platform


class JotulEntitySensorExtension:
    """Extension de capteur jotul."""

    def __init__(self, label, get_op, result_key_name) -> None:
        """Init."""
        self.label = label
        self.get_op = get_op
        self.result_key_name = result_key_name

DOMAIN = "jotul"
INTERVAL = timedelta(seconds=30)
INTERVAL_CNTR = timedelta(seconds=300)  # Interval for check counters
TIMEOUT = 10
QUERY_STRING_BASE = "http://(HOST)/cgi-bin/sendmsg.lua"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT]

ATTR_AMBIENT_TEMPERATURE = "ambient_temperature"
ATTR_PELLET_TEMPERATURE = "pellet_temperature"
ATTR_SMOKE_TEMPERATURE = "smoke_temperature"
ATTR_CHRONO_STATUS = "chrono_status"
ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_TARGET_PRESSURE = "target_pressure"
ATTR_MEASURED_PRESSURE = "mesured_pressure"
ATTR_SMOKE_FAN_SPEED = "smoke_fan_speed"
ATTR_DETAILED_STATUS = "detailes_status"
ATTR_UNIT_RPM = "RPM"
ATTR_DETAILED_STATUS_OPTIONS = [
    "OFF",
    "OFF TIMER",
    "TESTFIRE",
    "HEATUP",
    "FUELIGN",
    "IGNTEST",
    "BURNING",
    "COOLFLUID",
    "FIRESTOP",
    "CLEANFIRE",
    "COOL",
    "CHIMNEY ALARM",
    "GRATE ERROR",
    "NTC2 ALARM",
    "NTC3 ALARM",
    "DOOR ALARM",
    "PRESS ALARM",
    "NTC1 ALARM",
    "TC1 ALARM",
    "GAS ALARM",
    "NOPELLET ALARM",
]

ATTR_DETAILED_STATUS_OPTIONS_MAPPING : dict[int, str] = {
            0: "OFF",
            1: "OFF TIMER",
            2: "TESTFIRE",
            3: "HEATUP",
            4: "FUELIGN",
            5: "IGNTEST",
            6: "BURNING",
            9: "COOLFLUID",
            10: "FIRESTOP",
            11: "CLEANFIRE",
            12: "COOL",
            241: "CHIMNEY ALARM",
            243: "GRATE ERROR",
            244: "NTC2 ALARM",
            245: "NTC3 ALARM",
            247: "DOOR ALARM",
            248: "PRESS ALARM",
            249: "NTC1 ALARM",
            250: "TC1 ALARM",
            252: "GAS ALARM",
            253: "NOPELLET ALARM",
        }

ATTR_FAN_LEVEL_MAPPING : dict[int, str] = {
    0: "Off",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "Max",
    7: "Auto"
}
ATTR_FAN_LEVEL_MAPING_REVERSE : dict[str, int] = {
    "Off" : 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "Max": 6,
    "Auto": 7
}

# ATTR_STATE_ON = "on"
# ATTR_STATE_OFF = "off"

ATTR_DICT_INF_SENSOR: dict[str, JotulEntitySensorExtension] = {
    ATTR_AMBIENT_TEMPERATURE : JotulEntitySensorExtension("Température ambiante", "GET TMPS", "T1"),
    ATTR_PELLET_TEMPERATURE : JotulEntitySensorExtension("Température du pellet", "GET TMPS", "T2"),
    ATTR_SMOKE_TEMPERATURE : JotulEntitySensorExtension("Température des fumées", "GET TMPS", "T3"),
    ATTR_TARGET_PRESSURE : JotulEntitySensorExtension("Pression souhaité", "GET DPRS", "DPT"),
    ATTR_MEASURED_PRESSURE : JotulEntitySensorExtension("Pression mesurée", "GET DPRS", "DP"),
    ATTR_SMOKE_FAN_SPEED : JotulEntitySensorExtension("Vitesse de ventilation des fumées", "GET FAND", "F1RPM"),
    ATTR_DETAILED_STATUS : JotulEntitySensorExtension("Statut détaillé du poel", "", "STATUS_TXT")
    }
