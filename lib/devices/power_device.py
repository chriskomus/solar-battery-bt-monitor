# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging


class PowerDevice:
    """
    General class for different PowerDevices
    Stores the values read from the devices with the best available resolution (milli-whatever)
    Temperature is stored as /10 kelvin
    Soc is stored as /10 %
    Most setters will validate the input to guard against false Zero-values
    """

    def __init__(self, parent=None):
        logging.debug("New PowerDevice")
        self._parent = parent
        self._cell_mvoltage = {}
        self._power_switch = 0
        self._dsoc = {"val": 0, "min": 1, "max": 1000, "maxdiff": 200}
        self._dkelvin = {"val": 2731, "min": 1731, "max": 3731, "maxdiff": 20}
        self._bkelvin = {"val": 2731, "min": 1731, "max": 3731, "maxdiff": 20}
        self._mcapacity = {"val": 0, "min": 0, "max": 250000, "maxdiff": 20000}
        self._mcurrent = {"val": 0, "min": 0, "max": 30000, "maxdiff": 10000}
        self._mpower = {"val": 0, "min": 0, "max": 200000, "maxdiff": 100000}
        self._mvoltage = {"val": 0, "min": 0, "max": 48000, "maxdiff": 12000}
        self._input_mcurrent = {"val": 0, "min": 0, "max": 30000, "maxdiff": 10000}
        self._input_mpower = {"val": 0, "min": 0, "max": 200000, "maxdiff": 100000}
        self._input_mvoltage = {"val": 0, "min": 0, "max": 48000, "maxdiff": 12000}
        self._charge_mcurrent = {"val": 0, "min": 0, "max": 30000, "maxdiff": 10000}
        self._charge_mpower = {"val": 0, "min": 0, "max": 200000, "maxdiff": 100000}
        self._charge_mvoltage = {"val": 0, "min": 0, "max": 48000, "maxdiff": 12000}
        self._mvoltage = {"val": 0, "min": 0, "max": 15000, "maxdiff": 15000}
        self._msg = None
        self._status = None

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, value):
        self._device_id = int(value)

    @property
    def need_polling(self):
        return self._need_polling

    @need_polling.setter
    def need_polling(self, value):
        if value == True:
            logging.info("Enabling BLE-polling")
        self._need_polling = value

    @property
    def send_ack(self):
        return self._send_ack

    @send_ack.setter
    def send_ack(self, value):
        self._send_ack = value

    @property
    def poll_register(self):
        return self._poll_register

    @poll_register.setter
    def poll_register(self, value):
        self._poll_register = value

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self.parent.logger_name

    def alias(self):
        return self.parent.alias()

    @property
    def datalogger(self):
        return self.parent.datalogger

    @property
    def dsoc(self):
        return self._dsoc["val"]

    @dsoc.setter
    def dsoc(self, value):
        self.validate("_dsoc", value)

    @property
    def soc(self):
        return self.dsoc / 10

    @soc.setter
    def soc(self, value):
        self.dsoc = value * 10

    @property
    def temperature(self):
        return self._dkelvin["val"]

    @temperature.setter
    def temperature(self, value):
        self.validate("_dkelvin", value)

    @property
    def battery_temperature(self):
        return self._bkelvin["val"]

    @battery_temperature.setter
    def battery_temperature(self, value):
        self.validate("_bkelvin", value)

    @property
    def temperature_celsius(self):
        return round((self.temperature - 2731) * 0.1, 1)

    @temperature_celsius.setter
    def temperature_celsius(self, value):
        self.temperature = (value * 10) + 2731

    @property
    def temperature_fahrenheit(self):
        return round(((self.temperature * 0.18) - 459.67), 1)

    @temperature_fahrenheit.setter
    def temperature_fahrenheit(self, value):
        self.temperature = (value + 459.67) * (5 / 9) * 10

    @property
    def battery_temperature_celsius(self):
        return round((self.battery_temperature - 2731) * 0.1, 1)

    @battery_temperature_celsius.setter
    def battery_temperature_celsius(self, value):
        self.battery_temperature = (value * 10) + 2731

    @property
    def battery_temperature_fahrenheit(self):
        return round(((self.temperature * 0.18) - 459.67), 1)

    @battery_temperature_fahrenheit.setter
    def battery_temperature_fahrenheit(self, value):
        self.temperature = (value + 459.67) * (5 / 9) * 10

    @property
    def mcapacity(self):
        return self._mcapacity["val"]

    @mcapacity.setter
    def mcapacity(self, value):
        self.validate("_mcapacity", value)

    @property
    def capacity(self):
        return round(self.mcapacity / 1000, 1)

    @capacity.setter
    def capacity(self, value):
        self.mcapacity = value * 1000

    # Voltage
    @property
    def mvoltage(self):
        return self._mvoltage["val"]

    @mvoltage.setter
    def mvoltage(self, value):
        self.validate("_mvoltage", value)

    @property
    def voltage(self):
        return round(self.mvoltage / 1000, 1)

    @voltage.setter
    def voltage(self, value):
        self.mvoltage = value * 1000

    @property
    def input_mvoltage(self):
        return self._input_mvoltage["val"]

    @input_mvoltage.setter
    def input_mvoltage(self, value):
        self.validate("_input_mvoltage", value)

    @property
    def input_voltage(self):
        return round(self.input_mvoltage / 1000, 1)

    @input_voltage.setter
    def input_voltage(self, value):
        self.input_mvoltage = value * 1000

    @property
    def charge_mvoltage(self):
        return self._charge_mvoltage["val"]

    @charge_mvoltage.setter
    def charge_mvoltage(self, value):
        self.validate("_charge_mvoltage", value)

    @property
    def charge_voltage(self):
        return round(self.charge_mvoltage / 1000, 1)

    @charge_voltage.setter
    def charge_voltage(self, value):
        self.charge_mvoltage = value * 1000

    # current
    @property
    def mcurrent(self):
        return self._mcurrent["val"]

    @mcurrent.setter
    def mcurrent(self, value):
        self.validate("_mcurrent", value)

    @property
    def current(self):
        return round(self.mcurrent / 1000, 1)

    @current.setter
    def current(self, value):
        self.mcurrent = value * 1000

    @property
    def input_mcurrent(self):
        return self._input_mcurrent["val"]

    @input_mcurrent.setter
    def input_mcurrent(self, value):
        self.validate("_input_mcurrent", value)

    @property
    def input_current(self):
        return round(self.input_mcurrent / 1000, 1)

    @input_current.setter
    def input_current(self, value):
        self.input_mcurrent = value * 1000

    @property
    def charge_mcurrent(self):
        return self._charge_mcurrent["val"]

    @charge_mcurrent.setter
    def charge_mcurrent(self, value):
        self.validate("_charge_mcurrent", value)

    @property
    def charge_current(self):
        return round(self.charge_mcurrent / 1000, 1)

    @charge_current.setter
    def charge_current(self, value):
        self.charge_mcurrent = value * 1000

    # power
    @property
    def mpower(self):
        return self._mpower["val"]

    @mpower.setter
    def mpower(self, value):
        self.validate("_mpower", value)

    @property
    def power(self):
        return round(self.mpower / 1000, 1)

    @power.setter
    def power(self, value):
        self.mpower = value * 1000

    @property
    def input_mpower(self):
        return self._input_mpower["val"]

    @input_mpower.setter
    def input_mpower(self, value):
        self.validate("_input_mpower", value)

    @property
    def input_power(self):
        return round(self.input_mpower / 1000, 1)

    @input_power.setter
    def input_power(self, value):
        self.input_mpower = value * 1000

    @property
    def charge_mpower(self):
        return self._charge_mpower["val"]

    @charge_mpower.setter
    def charge_mpower(self, value):
        self.validate("_charge_mpower", value)

    @property
    def charge_power(self):
        return round(self.charge_mpower / 1000, 1)

    @charge_power.setter
    def charge_power(self, value):
        self.charge_mpower = value * 1000

    @property
    def power_switch(self):
        return self._power_switch

    @power_switch.setter
    def power_switch(self, value):
        if str(value).lower() == "on":
            value = 1
        if str(value).lower() == "off":
            value = 0
        if value != self._power_switch:
            self._power_switch = value
            try:
                self.datalogger.log(self.logger_name, "power_switch", self.power_switch)
            except:
                pass

    @property
    def msg(self):
        return self._msg

    @msg.setter
    def msg(self, message):
        self._msg = message

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def dumpAll(self):
        out = "RAW "
        for var in self.__dict__:
            if var != "_msg":
                out = "{} {} == {},".format(out, var, self.__dict__[var])
        logging.debug(out)

    def validate(self, var, val):
        definition = getattr(self, var)
        val = float(val)
        if val == definition["val"]:
            logging.debug(
                "[{}] Value of {} out of bands: Changed from {} to {} (no diff)".format(
                    self.name, var, definition["val"], val
                )
            )
            return False
        if val > definition["max"]:
            logging.warning(
                "[{}] Value of {} out of bands: Changed from {} to {} (> max {})".format(
                    self.name, var, definition["val"], val, definition["max"]
                )
            )
            return False
        if val < definition["min"]:
            logging.warning(
                "[{}] Value of {} out of bands: Changed from {} to {} (< min {})".format(
                    self.name, var, definition["val"], val, definition["min"]
                )
            )
            return False
        if (definition["val"] != 0 and definition["val"] != 2731) and abs(
            val - definition["val"]
        ) > definition["maxdiff"]:
            logging.warning(
                "[{}] Value of {} out of bands: Changed from {} to {} (> maxdiff {})".format(
                    self.name, var, definition["val"], val, definition["maxdiff"]
                )
            )
            return False
        logging.debug(
            "[{}] Value of {} changed from {} to {}".format(
                self.name, var, definition["val"], val
            )
        )
        self.__dict__[var]["val"] = val
