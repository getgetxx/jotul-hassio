from config.custom_components.jotul import JotulApi
from homeassistant.components.switch import SwitchEntity


class JotulOnOffSwitch(SwitchEntity):
    """On off Jotul state"""

    _attr_icon= "mdi:fireplace"
    _attr_should_poll= True
    _attr_name = "Etat"
    _attr_has_entity_name = True


    def __init__(self, api: JotulApi) -> None:
        """Initialize Jotul on off switch."""
        self._api = api
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.device.mac}-streamer"
