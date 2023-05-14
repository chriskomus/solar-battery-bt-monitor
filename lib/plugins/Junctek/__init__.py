# ------------------------------------------------------
# Original Author: Chris Komus
# https://github.com/chriskomus/solar-battery-bt-monitor
#
# ------------------------------------------------------
import os
from threading import Timer
import logging
import time

from lib.solar_device import SolarDeviceManager, SolarDevice


class Config:
    SYSTEM_TIMEOUT = 15  # exit program after this (seconds)
    DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

    NOTIFY_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

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
    def __init__(
        self,
        # alias=None,
        # on_data_received=None,
        # auto_reconnect=False,
        # continuous=False,
        # interval=-1,
        # battery_capacity_ah=100,
        # start_script_as_charging=False,
        logger_name=None,
        config=None,
    ):
        # self.adapter_name = adapter_name
        # self.mac_address = mac_address
        # self.alias = alias
        # self.data_callback = on_data_received
        # self.auto_reconnect = auto_reconnect
        # self.continuous = continuous
        # self.interval = interval
        # self.device = None
        # self.manager = SolarDeviceManager(adapter_name=adapter_name)
        # self.device = SolarDevice(
        #     mac_address=mac_address,
        #     manager=self.manager,
        #     on_resolved=self.on_resolved,
        #     on_data=self.on_data_received,
        #     auto_reconnect=auto_reconnect,
        #     notify_char_uuid=Config().NOTIFY_CHAR_UUID,
        #     notify_service_uuid=Config().NOTIFY_SERVICE_UUID,
        #     need_polling=continuous,
        #     logger_name="junctek",
        #     config=config,
        # )
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

        # self.timer = None
        # if not self.continuous:
        #     self.timer = Timer(SYSTEM_TIMEOUT, self.gracefully_exit)
        #     self.timer.start()
        self.data = {}

        # if not self.manager.is_adapter_powered:
        #     self.manager.is_adapter_powered = True
        # logging.info(
        #     "Adapter status - Powered: {}".format(self.manager.is_adapter_powered)
        # )

    # def connect(self):
    #     discovering = True
    #     wait = Config().DISCOVERY_TIMEOUT
    #     found = False

    #     self.manager.update_devices()
    #     logging.info("Starting discovery...")
    #     self.manager.start_discovery()

    #     while discovering:
    #         time.sleep(1)
    #         logging.info("Devices found: %s", len(self.manager.devices()))
    #         for dev in self.manager.devices():
    #             if dev.mac_address == self.mac_address or dev.alias() == self.alias:
    #                 logging.info(
    #                     "Found bt1 device %s  [%s]", dev.alias(), dev.mac_address
    #                 )
    #                 discovering = False
    #                 found = True
    #         wait = wait - 1
    #         if wait <= 0:
    #             discovering = False
    #     self.manager.stop_discovery()

    #     if found:
    #         self._connect()
    #     else:
    #         logging.error(
    #             "Device not found: [%s], please check the details provided.",
    #             self.mac_address,
    #         )
    #         self.gracefully_exit(True)

    # def _connect(self):
    #     try:
    #         self.device.connect()
    #         self.manager.run()
    #     except Exception as e:
    #         logging.error(e)
    #         self.gracefully_exit(True)
    #     except KeyboardInterrupt:
    #         self.gracefully_exit()

    def on_resolved(self):
        logging.debug("resolved services")

    # def on_data_received(self, value):
    #     logging.debug("junctek data received!")
    #     bs = str(value.hex()).upper()
    #     logging.debug(bs)
    #     if not self.validate(bs):
    #         return False

    #     data = self.parse_incoming_bytestream(
    #         bs, self.battery_capacity_ah, self.charging
    #     )
    #     for key in data:
    #         self.data[key] = data[key]

    #     if self.data_callback is not None:
    #         self.data_callback(self.data)

    #     if self.continuous and self.interval > 0:
    #         logging.info("Query Junctek again in {} seconds...".format(self.interval))
    #         time.sleep(self.interval)
    #         self.request_data()

    def on_data_received(self, value):
        # logging.debug("junctek data received!")
        bs = str(value.hex()).upper()
        if not self.validate(bs):
            return None

        data = self.parse_incoming_bytestream(
            bs, self.battery_capacity_ah, self.charging
        )
        for key in data:
            self.data[key] = data[key]

        return self.data

        # if self.data_callback is not None:
        #     self.data_callback(self.data)

        # if self.continuous and self.interval > 0:
        #     logging.info("Query Junctek again in {} seconds...".format(self.interval))
        #     time.sleep(self.interval)
        #     self.request_data()

    # def gracefully_exit(self, connectFailed=False):
    #     logging.info("gracefully_exit")
    #     # if self.timer is not None and self.timer.is_alive():
    #     #     self.timer.cancel()
    #     if self.device is not None and not connectFailed and self.device.is_connected():
    #         logging.info(
    #             "Exit: Disconnecting device: %s [%s]",
    #             self.device.alias(),
    #             self.device.mac_address,
    #         )
    #         self.device.disconnect()
    #     self.manager.stop()
    #     os._exit(os.EX_OK)

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
            # logging.debug("No parameters found in stream: {}".format(bs))
            return False

        return True

    def parse_incoming_bytestream(self, bs, battery_capacity_ah, charging):
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

        # logging.debug(bs_list_rev)

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
                    charging = True
                else:
                    charging = False
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
        if charging:
            values["junctek_load_status"] = 1
        else:
            values["junctek_load_status"] = 0
            if "junctek_load_amps" in values:
                values["junctek_load_amps"] *= -1
            if "junctek_load_power_watts" in values:
                values["junctek_load_power_watts"] *= -1

        # Calculate percentage
        if "junctek_ah_remaining" in values:
            values["junctek_battery_percentage"] = (
                values["junctek_ah_remaining"] / battery_capacity_ah * 100
            )

        # Append max capacity
        values["junctek_max_capacity"] = battery_capacity_ah

        return values
