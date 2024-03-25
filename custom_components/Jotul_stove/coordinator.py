"""The ecoforest coordinator."""


import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import POLLING_INTERVAL, TIMEOUT

_LOGGER = logging.getLogger(__name__)


class JotulCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant | None, my_api) -> None :
        """Initialize Jotul sensors coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Jotul",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=POLLING_INTERVAL,
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
            async with asyncio.timeout(TIMEOUT):
                return await self.my_api.async_get_alls()
        except BaseException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
