# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging
from lib.devices.battery_device import BatteryDevice


class MonitoringDevice(BatteryDevice):
    """
    Special class for Battery Monitoring Devices.
    Extending BatteryDevice class with more properties specifically for the battery monitor
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logging.debug("New MonitoringDevice")
        self._mpower = {"val": 0, "min": -500000, "max": 500000, "maxdiff": 400000}

    @property
    def mins_remaining(self):
        return self._mins_remaining

    @mins_remaining.setter
    def mins_remaining(self, value):
        self._mins_remaining = value
