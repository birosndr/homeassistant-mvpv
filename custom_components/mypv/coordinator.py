"""Provides the MYPV DataUpdateCoordinator."""
from datetime import timedelta
import logging
import requests
import json
from datetime import date

from async_timeout import timeout
from homeassistant.util.dt import utcnow
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MYPVDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MYPV data."""

    def __init__(self, hass: HomeAssistant, *, config: dict, options: dict):
        """Initialize global NZBGet data updater."""
        self._host = config[CONF_HOST]
        self._info = None
        self._setup = None
        self._next_update = 0
        update_interval = timedelta(seconds=10)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from NZBGet."""

        def _update_data() -> dict:
            """Fetch data from NZBGet via sync functions."""
            data = self.data_update()
            if self._info is None:
                self._info = self.info_update()

            if self._setup is None or self._next_update < utcnow().timestamp():
                self._next_update = utcnow().timestamp() + 150  # 86400
                self._setup = self.setup_update()

            return {
                "data": data,
                "info": self._info,
                "setup": self._setup,
            }

        try:
            async with timeout(20):
                return await self.hass.async_add_executor_job(_update_data)
        except Exception as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error

    def data_update(self):
        """Update inverter data."""
        try:
            response = requests.get(f"http://{self._host}/data.jsn")
            data = json.loads(response.text)

            today = date.today()
            response = requests.get(f"http://{self._host}/chart.jsn?chd=1&chm=" + str(today.month) + "&chy="+ today.strftime("%y") +"&chpl=31&cht=4&cha=0&chp1=5&chp2=6")
            chartData = json.loads(response.text)
            data['ret_grid_power'] = int(chartData['5'].split(',')[today.day - 1])
            data['grid_power_consumption'] = abs(int(chartData['6'].split(',')[today.day - 1]))

            response = requests.get(f"http://{self._host}/chart.jsn?chd=1&chm=" + str(today.month) + "&chy="+ today.strftime("%y") +"&chpl=31&cht=4&cha=0&chp1=3&chp2=4")
            chartData = json.loads(response.text)
            data['energy_consumption'] = int(chartData['3'].split(',')[today.day - 1]) + int(chartData['4'].split(',')[today.day - 1])

            _LOGGER.debug(data)
            return data
        except Exception as error:
            raise UpdateFailed(f"Invalid response from data_update: {error}") from error

    def info_update(self):
        """Update inverter info."""
        try:
            response = requests.get(f"http://{self._host}/mypv_dev.jsn")
            info = json.loads(response.text)
            _LOGGER.debug(info)
            return info
        except:
            raise UpdateFailed(f"Invalid response from info_update: {error}") from error

    def setup_update(self):
        """Update inverter info."""
        try:
            response = requests.get(f"http://{self._host}/setup.jsn")
            info = json.loads(response.text)
            _LOGGER.debug(info)
            return info
        except:
            raise UpdateFailed(f"Invalid response from setup_update: {error}") from error
