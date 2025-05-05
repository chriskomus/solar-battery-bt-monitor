# ------------------------------------------------------
# Original Author: Olen, Scott Nichol, Cyril Sebastian
# ------------------------------------------------------
import logging
import libscrc


class Config:
    SYSTEM_TIMEOUT = 15  # exit program after this (seconds)
    DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

    READ_PARAMS = {
        "DEVICE_ID": 255,
        "FUNCTION": 3,  # read: 3, write: 6
        "REGISTER": 256,
        "WORDS": 34,
    }

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
        logger_name=None,
        config=None,
    ):
        self.logger_name = logger_name
        self.config = config

        self.data = {}

    def poll_request(self):
        return self.create_request_payload(
            Config().READ_PARAMS["DEVICE_ID"],
            Config().READ_PARAMS["FUNCTION"],
            Config().READ_PARAMS["REGISTER"],
            Config().READ_PARAMS["WORDS"],
        )

    def on_resolved(self):
        logging.debug("resolved services")
        self.request_data()

    def on_data_received(self, value):
        data = self.parse_incoming_bytestream(value)
        for key in data:
            self.data[key] = data[key]

        return self.data

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
