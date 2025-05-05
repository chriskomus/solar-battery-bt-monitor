# ------------------------------------------------------
# Original Author: Chris Komus
# https://github.com/chriskomus/solar-battery-bt-monitor
#
# ------------------------------------------------------
import logging
from collections import deque
import time


class Config:
    SYSTEM_TIMEOUT = 15  # exit program after this (seconds)
    DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

    NOTIFY_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
    WAIT_TO_SEND = True

    BEGINNING_OF_STREAM = "BB"
    END_OF_STREAM = "EE"
    PARAM_KEYS = {
        "junctek_load_volts": "C0",
        "junctek_load_amps": "C1",
        "junctek_load_status": "D1",
        "junctek_ah_remaining": "D2",
        "junctek_min_remaining": "D6",
        "junctek_load_power_watts": "D8",
        "junctek_temp": "D9",
    }


class Util:
    min_remaining_history = deque()

    def __init__(
        self,
        logger_name=None,
        config=None,
    ):
        self.logger_name = logger_name
        self.config = config

        if self.config:
            self.battery_capacity_ah = self.config.getint(
                self.logger_name, "battery_capacity_ah", fallback=100
            )
            self.charging = self.config.getboolean(
                self.logger_name, "start_script_as_charging", fallback=False
            )
            self.draw_as_negative_value = self.config.getboolean(
                self.logger_name, "draw_as_negative_value", fallback=False
            )
        else:
            raise ValueError("[{}] Missing config".format(self.logger_name))

        self.data = {}

    def on_resolved(self):
        logging.debug("resolved services")

    def on_data_received(self, value):
        bs = str(value.hex()).upper()
        if not self.validate(bs):
            return None

        data = self.parse_incoming_bytestream(bs, self.battery_capacity_ah)
        for key in data:
            self.data[key] = data[key]

        return self.data

    def validate(self, bs):
        """
        Validate that the data has a valid start of stream and end of stream,
        and contains at least one known parameter.
        """
        if bs == None:
            logging.warning("Empty BS {}".format(bs))
            return False

        if not bs.startswith(Config().BEGINNING_OF_STREAM):
            logging.warning("Incorrect beginning of stream: {}".format(bs))
            return False

        if not bs.endswith(Config().END_OF_STREAM):
            logging.warning("Incorrect end of stream: {}".format(bs))
            return False

        if not [v for v in Config().PARAM_KEYS.values() if v in bs]:
            return False

        return True

    def parse_incoming_bytestream(self, bs, battery_capacity_ah):
        """
        Get raw values from the bytestream:

        Returns a dict containing any keys in Parameters().PARAM_KEYS
        and raw values found in the bytestream.

        Bytestreams are varying lengths, with hex keys and decimal values, and follow this format:
        [starting byte] [dec value] [hex param key] ... [dec value] [hex param key] ... [checksum] [ending byte]

        The value precedes the hex parameter key.
        ie: 12.32v would be: 1232C0, where 1232=12.32v and C0=voltage param key

        To modify or add new parameters, change Parameters().PARAM_KEYS. This function will grab any new values it
        finds that can be associated with a param key.
        """
        # params = [i for i in self.Parameters().PARAM_KEYS.values()]
        params_keys = list(Config().PARAM_KEYS.keys())
        params_values = list(Config().PARAM_KEYS.values())

        # split bs into a list of all values and hex keys
        bs_list = [bs[i : i + 2] for i in range(0, len(bs), 2)]

        # reverse the list so that values come after hex params
        bs_list_rev = list(reversed(bs_list))

        values = {}
        # iterate through the list and if a param is found,
        # add it as a key to the dict. The value for that key is a
        # concatenation of all following elements in the list
        # until a non-numeric element appears. This would either
        # be the next param or the beginning hex value.
        for i in range(len(bs_list_rev) - 1):
            if bs_list_rev[i] in params_values:
                value_str = ""
                j = i + 1
                while j < len(bs_list_rev) and bs_list_rev[j].isdigit():
                    value_str = bs_list_rev[j] + value_str
                    j += 1

                position = params_values.index(bs_list_rev[i])

                key = params_keys[position]
                values[key] = value_str

        # Format the value to the right decimal place, or perform other formatting
        for key, value in list(values.items()):
            if not value.isdigit():
                del values[key]

            val_int = int(value)
            if key == "junctek_load_volts":
                values[key] = val_int / 100
            elif key == "junctek_load_amps":
                values[key] = val_int / 100
            elif key == "junctek_load_status":
                if value == "01":
                    self.charging = True
                else:
                    self.charging = False
            elif key == "junctek_ah_remaining":
                values[key] = val_int / 1000
            elif key == "junctek_min_remaining":
                values[key] = val_int
            elif key == "junctek_load_power_watts":
                values[key] = val_int / 100
            elif key == "junctek_temp":
                values[key] = val_int - 100

        # Display current as negative numbers if discharging
        # Update junctek_load_status value to int
        if self.charging:
            values["junctek_load_status"] = 1
            if "junctek_load_amps" in values:
                values["junctek_load_amps"] *= -1
            if "junctek_load_power_watts" in values:
                values["junctek_load_power_watts"] *= -1
        else:
            values["junctek_load_status"] = 0

        # Calculate percentage
        if "junctek_ah_remaining" in values:
            values["junctek_battery_percentage"] = (
                values["junctek_ah_remaining"] / battery_capacity_ah * 100
            )

        # Calculate minutes remaining by taking avg of recent junctek_min_remaining values
        if "junctek_min_remaining" in values:
            now = time.time()
            expiry_seconds = (
                self.config.getint(
                    self.logger_name, "min_remaining_avg_time_in_mins", fallback=10
                )
                * 60
            )

            self.min_remaining_history.append((now, values["junctek_min_remaining"]))

            while (
                self.min_remaining_history
                and now - self.min_remaining_history[0][0] > expiry_seconds
            ):
                self.min_remaining_history.popleft()

            if self.min_remaining_history:
                valid_values = [v for _, v in self.min_remaining_history]
                values["junctek_min_remaining"] = sum(valid_values) / len(valid_values)

        # Append max capacity
        values["junctek_max_capacity"] = battery_capacity_ah

        return values
