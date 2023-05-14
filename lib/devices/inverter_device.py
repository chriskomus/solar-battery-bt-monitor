# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging
from lib.devices.power_device import PowerDevice


class InverterDevice(PowerDevice):
    """
    Special class for Regulator-devices.  (DC-AC)
    Extending PowerDevice class with more properties specifically for the regulators
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logging.debug("New InverterDevice")
        self._input_mvoltage = {"val": 0, "min": 0, "max": 50000, "maxdiff": 50000}
        self._mvoltage = {"val": 0, "min": 0, "max": 250000, "maxdiff": 250000}
