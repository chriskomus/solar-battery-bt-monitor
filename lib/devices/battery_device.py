# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
import logging
from lib.devices.power_device import PowerDevice


class BatteryDevice(PowerDevice):
    """
    Special class for Battery-devices.
    Extending PowerDevice class with more properties specifically for the batteries
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        logging.debug("New BatteryDevice")
        self._health = None
        self._state = None
        self._mcurrent = {"val": 0, "min": -500000, "max": 500000, "maxdiff": 400000}
        self._max_capacity = {"val": 0, "min": 0, "max": 400, "maxdiff": 5}
        self._exp_capacity = {"val": 0, "min": 0, "max": 400, "maxdiff": 5}
        self._mvoltage = {"val": 0, "min": 10000, "max": 15000, "maxdiff": 12000}
        self._charge_cycles = {"val": 0, "min": 0, "max": 10000, "maxdiff": 1}
        i = 0
        while i < 16:
            i = i + 1
            self._cell_mvoltage[i] = {
                "val": 0,
                "min": 2000,
                "max": 4000,
                "maxdiff": 500,
            }

    @property
    def charge_cycles(self):
        return self._charge_cycles["val"]

    @charge_cycles.setter
    def charge_cycles(self, value):
        self.validate("_charge_cycles", value)
        if value > 0:
            was = self.health
            if value > 2000:
                self._health = "good"
            else:
                self._health = "perfect"
            self.health_changed(was)

    @property
    def mcurrent(self):
        return super().mcurrent

    @property
    def current(self):
        return super().current

    @mcurrent.setter
    def mcurrent(self, value):
        super(BatteryDevice, self.__class__).mcurrent.fset(self, value)
        if value == 0 and (self.mcurrent > 500 or self.mcurrent < -500):
            return
        was = self.state
        if value > 20:
            self._state = "charging"
        elif value < -20:
            self._state = "discharging"
        else:
            self._state = "standby"
        self.state_changed(was)

    @current.setter
    def current(self, value):
        super(BatteryDevice, self.__class__).current.fset(self, value)
        if value == 0 and (self.mcurrent > 500 or self.mcurrent < -500):
            return
        was = self.state
        if value > 0.02:
            self._state = "charging"
        elif value < -0.02:
            self._state = "discharging"
        else:
            self._state = "standby"
        self.state_changed(was)

    @property
    def cell_mvoltage(self):
        return self._cell_mvoltage

    @cell_mvoltage.setter
    def cell_mvoltage(self, value):
        cell = value[0]
        new_value = value[1]
        current_value = self._cell_mvoltage[cell]["val"]
        if new_value > 0 and abs(new_value - current_value) > 10:
            self._cell_mvoltage[cell]["val"] = new_value

    @property
    def cell_voltage(self):
        cell_array = {}
        for cell in self._cell_mvoltage:
            cell_array[cell] = {"val": (self._cell_mvoltage[cell]["val"] * 0.001)}
        return cell_array

    @cell_voltage.setter
    def cell_voltage(self, value):
        cell = value[0]
        new_value = value[1] * 1000
        current_value = self._cell_mvoltage[cell]["val"]
        if new_value > 0 and abs(new_value - current_value) > 10:
            self._cell_mvoltage[cell]["val"] = new_value

    @property
    def afestatus(self):
        return self._afestatus

    @afestatus.setter
    def afestatus(self, value):
        self._afestatus = value

    @property
    def max_capacity(self):
        return self._max_capacity["val"]

    @max_capacity.setter
    def max_capacity(self, value):
        self.validate("_max_capacity", value)

    @property
    def exp_capacity(self):
        return self._exp_capacity["val"]

    @exp_capacity.setter
    def exp_capacity(self, value):
        self.validate("_exp_capacity", value)

    @property
    def health(self):
        return self._health

    @property
    def state(self):
        return self._state

    def state_changed(self, was):
        if was != self.state:
            logging.info(
                "[{}] Value of {} changed from {} to {}".format(
                    self.name, "state", was, self.state
                )
            )

    def health_changed(self, was):
        if was != self.health:
            logging.info(
                "[{}] Value of {} changed from {} to {}".format(
                    self.name, "health", was, self.health
                )
            )
