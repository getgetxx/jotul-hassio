"""Config flow."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ALIAS, CONF_HOST

from .const import DOMAIN


class JotulConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Jotul config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the Jotul config flow."""
        self.host: str | None = None
        self.alias: str | None = None

    @property
    def schema(self) -> vol.Schema:
        """Return current schema."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=self.host): str,
                vol.Optional(CONF_ALIAS): str,
            }
        )

    async def async_step_user(self, user_input):
        """Describe the user step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self.schema)

        self.host = user_input.get(CONF_HOST)
        self.alias = user_input.get(CONF_ALIAS)
        return self.async_create_entry(title=self.alias, data=user_input)
