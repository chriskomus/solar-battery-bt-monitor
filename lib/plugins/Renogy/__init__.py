# ------------------------------------------------------
# Original Author: Olen, Scott Nichol, Cyril Sebastian
# ------------------------------------------------------
import os
from threading import Timer
import logging
import time
import libscrc

from lib.solar_device import SolarDeviceManager, SolarDevice


class Config:
    SYSTEM_TIMEOUT = 15  # exit program after this (seconds)
    DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

    READ_PARAMS = {
        "DEVICE_ID": 255,
        "FUNCTION": 3,  # read: 3, write: 6
        "REGISTER": 256,
        "WORDS": 34,
    }

    # old
    # NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
    # WRITE_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"

    # new
    NOTIFY_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
    WRITE_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
    WRITE_CHAR_UUID_POLLING = "0000ffd1-0000-1000-8000-00805f9b34fb"
    WRITE_CHAR_UUID_COMMANDS = "0000ffd1-0000-1000-8000-00805f9b34fb"
    NEED_POLLING = True

    # for reference in grafana
    CHARGING_STATE = {
        0: "deactivated",
        1: "activated",
        2: "mppt",
        3: "equalizing",
        4: "boost",
        5: "floating",
        6: "current limiting",
    }
    LOAD_STATE = {0: "off", 1: "on"}
    FUNCTION = {3: "READ", 6: "WRITE"}


class Util:
    def __init__(
        self,
        # alias=None,
        # on_data_received=None,
        # auto_reconnect=False,
        # continuous=False,
        # interval=-1,
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
        #     write_char_uuid=Config().WRITE_CHAR_UUID,
        #     need_polling=continuous,
        #     logger_name="renogy",
        #     config=config,
        # )

        self.logger_name = logger_name
        self.config = config

        # if self.config:
        #     self.battery_capacity_ah = self.config.getint(self.logger_name, "battery_capacity_ah", fallback=100)
        #     self.charging = self.config.getboolean(self.logger_name, "start_script_as_charging", fallback=False)
        #     self.draw_as_negative_value = self.config.getboolean(self.logger_name, "draw_as_negative_value", fallback=False)
        # else:
        #     raise ValueError("[{}] Missing config".format(self.logger_name))

        # self.timer = None
        # if not self.continuous:
        #     self.timer = Timer(Config().SYSTEM_TIMEOUT, self.gracefully_exit)
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

    def poll_request(self):
        return self.create_request_payload(
            Config().READ_PARAMS["DEVICE_ID"],
            Config().READ_PARAMS["FUNCTION"],
            Config().READ_PARAMS["REGISTER"],
            Config().READ_PARAMS["WORDS"],
        )

    # def request_data(self):
    #     logging.debug("request_data...")
    #     request = self.create_request_payload(
    #         Config().READ_PARAMS["DEVICE_ID"],
    #         Config().READ_PARAMS["FUNCTION"],
    #         Config().READ_PARAMS["REGISTER"],
    #         Config().READ_PARAMS["WORDS"],
    #     )
    #     self.device.characteristic_write_value(request)

    def on_resolved(self):
        logging.debug("resolved services")
        self.request_data()

    # def on_data_received(self, value):
    #     logging.debug("renogy data received!")
    #     data = self.parse_incoming_bytestream(value)
    #     for key in data:
    #         self.data[key] = data[key]

    #     if self.data_callback is not None:
    #         self.data_callback(self.data)

    #     if self.continuous and self.interval > 0:
    #         logging.info("Query BT-1 again in {} seconds...".format(self.interval))
    #         time.sleep(self.interval)
    #         self.request_data()

    def on_data_received(self, value):
        # logging.debug("renogy data received!")
        data = self.parse_incoming_bytestream(value)
        for key in data:
            self.data[key] = data[key]

        return self.data

        # if self.data_callback is not None:
        #     self.data_callback(self.data)

        # if self.continuous and self.interval > 0:
        #     logging.info("Query BT-1 again in {} seconds...".format(self.interval))
        #     time.sleep(self.interval)
        #     self.request_data()

    # def gracefully_exit(self, connectFailed=False):
    #     logging.info("gracefully_exit")
    #     if self.timer is not None and self.timer.is_alive():
    #         self.timer.cancel()
    #     if self.device is not None and not connectFailed and self.device.is_connected():
    #         logging.info(
    #             "Exit: Disconnecting device: %s [%s]",
    #             self.device.alias(),
    #             self.device.mac_address,
    #         )
    #         self.device.disconnect()
    #     self.manager.stop()
    #     os._exit(os.EX_OK)

    def bytes_to_int(self, bs, offset, length):
        # Reads data from a list of bytes, and converts to an int
        # Bytes2Int(bs, 3, 2)
        ret = 0
        if len(bs) < (offset + length):
            return ret
        if length > 0:
            # offset = 11, length = 2 => 11 - 12
            byteorder = "big"
            start = offset
            end = offset + length
        else:
            # offset = 11, length = -2 => 10 - 11
            byteorder = "little"
            start = offset + length + 1
            end = offset + 1
        # Easier to read than the bitshifting below
        return int.from_bytes(bs[start:end], byteorder=byteorder)

    def int_to_bytes(self, i, pos=0):
        # Converts an integer into 2 bytes (16 bits)
        # Returns either the first or second byte as an int
        if pos == 0:
            return int(format(i, "016b")[:8], 2)
        if pos == 1:
            return int(format(i, "016b")[8:], 2)
        return 0

    def create_request_payload(self, device_id, function, regAddr, readWrd):
        data = None

        if regAddr:
            data = []
            data.append(device_id)
            data.append(function)
            data.append(self.int_to_bytes(regAddr, 0))
            data.append(self.int_to_bytes(regAddr, 1))
            data.append(self.int_to_bytes(readWrd, 0))
            data.append(self.int_to_bytes(readWrd, 1))

            crc = libscrc.modbus(bytes(data))
            data.append(self.int_to_bytes(crc, 1))
            data.append(self.int_to_bytes(crc, 0))
            logging.debug("{} {} => {}".format("create_request_payload", regAddr, data))
        return data

    def parse_incoming_bytestream(self, bs):
        data = {}
        data["function"] = self.bytes_to_int(bs, 1, 1)
        data["battery_percentage"] = self.bytes_to_int(bs, 3, 2)
        data["battery_voltage"] = self.bytes_to_int(bs, 5, 2) * 0.1
        data["battery_current"] = self.bytes_to_int(bs, 7, 2) * 0.01
        data["battery_temperature"] = self.parse_temperature(
            self.bytes_to_int(bs, 10, 1)
        )
        data["controller_temperature"] = self.parse_temperature(
            self.bytes_to_int(bs, 9, 1)
        )
        data["load_status"] = self.bytes_to_int(bs, 67, 1) >> 7
        data["load_voltage"] = self.bytes_to_int(bs, 11, 2) * 0.1
        data["load_current"] = self.bytes_to_int(bs, 13, 2) * 0.01
        data["load_power"] = self.bytes_to_int(bs, 15, 2)
        data["pv_voltage"] = self.bytes_to_int(bs, 17, 2) * 0.1
        data["pv_current"] = self.bytes_to_int(bs, 19, 2) * 0.01
        data["pv_power"] = self.bytes_to_int(bs, 21, 2)
        data["max_charging_power_today"] = self.bytes_to_int(bs, 33, 2)
        data["max_discharging_power_today"] = self.bytes_to_int(bs, 35, 2)
        data["charging_amp_hours_today"] = self.bytes_to_int(bs, 37, 2)
        data["discharging_amp_hours_today"] = self.bytes_to_int(bs, 39, 2)
        data["power_generation_today"] = self.bytes_to_int(bs, 41, 2)
        data["power_consumption_today"] = self.bytes_to_int(bs, 43, 2)
        data["power_generation_total"] = self.bytes_to_int(bs, 59, 4)
        data["charging_status"] = self.bytes_to_int(bs, 68, 1)
        return data

    def parse_set_load_response(self, bs):
        data = {}
        data["function"] = self.bytes_to_int(bs, 1, 1)
        data["load_status"] = self.bytes_to_int(bs, 5, 1)
        return data

    def parse_temperature(self, raw_value):
        sign = raw_value >> 7
        return -(raw_value - 128) if sign == 1 else raw_value
