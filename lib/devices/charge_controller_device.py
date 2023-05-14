# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging
from lib.devices.power_device import PowerDevice


class ChargeControllerDevice(PowerDevice):
    """
    Special class for ChargeController-devices.
    Extending PowerDevice class with more properties specifically for the charge controller
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logging.debug("New RegulatorDevice")

    def parse_notification(self, value):
        if self.deviceUtil.notificationUpdate(self.poll_register, value):
            # logging.debug("parse_notification {} success".format(self.poll_register))
            if (
                self.poll_register == "ParamSettingData"
                and len(self.deviceUtil.param_data) < 33
            ):
                pass
            else:
                self.poll_register = None
            return True
        else:
            logging.warning(
                "Error during parse_notification {}".format(self.poll_register)
            )
            self.poll_register = None
            return False
