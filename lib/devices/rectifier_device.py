# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging
from lib.devices.power_device import PowerDevice


class RectifierDevice(PowerDevice):
    """
    Special class for Rectifier-devices  (AC-DC).
    Extending PowerDevice class with more properties specifically for the regulators
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logging.debug("New RectifierDevice")
        self._input_mvoltage = {"val": 0, "min": 0, "max": 250000, "maxdiff": 250000}
        self._mvoltage = {"val": 0, "min": 0, "max": 50000, "maxdiff": 50000}
