# ------------------------------------------------------
# BTOneApp.py
# Original Author: Cyril Sebastian
# https://github.com/cyrils/renogy-bt1
#
# Modifications by: Scott Nichol
# ------------------------------------------------------
import os
from threading import Timer
import logging
import time

from lib.solar_device import SolarDeviceManager, SolarDevice
from lib.junctek.utils import parse_incoming_bytestream, validate

SYSTEM_TIMEOUT = 15  # exit program after this (seconds)
DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

NOTIFY_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"


class JunctekApp:
    def __init__(
        self,
        adapter_name,
        mac_address,
        alias=None,
        on_data_received=None,
        auto_reconnect=False,
        continuous=False,
        interval=-1,
        battery_capacity_ah=100,
        start_script_as_charging=False,
    ):
        self.adapter_name = adapter_name
        self.mac_address = mac_address
        self.alias = alias
        self.data_callback = on_data_received
        self.auto_reconnect = auto_reconnect
        self.continuous = continuous
        self.interval = interval
        self.device = None
        self.manager = SolarDeviceManager(adapter_name=adapter_name)
        self.device = SolarDevice(
            mac_address=mac_address,
            manager=self.manager,
            on_resolved=self.on_resolved,
            on_data=self.on_data_received,
            auto_reconnect=auto_reconnect,
            notify_char_uuid=NOTIFY_CHAR_UUID,
            notify_service_uuid=NOTIFY_SERVICE_UUID,
        )
        self.battery_capacity_ah = battery_capacity_ah
        self.charging = start_script_as_charging

        self.timer = None
        # if not self.continuous:
        #     self.timer = Timer(SYSTEM_TIMEOUT, self.gracefully_exit)
        #     self.timer.start()
        self.data = {}

        if not self.manager.is_adapter_powered:
            self.manager.is_adapter_powered = True
        logging.info(
            "Adapter status - Powered: {}".format(self.manager.is_adapter_powered)
        )

    def connect(self):
        discovering = True
        wait = DISCOVERY_TIMEOUT
        found = False

        self.manager.update_devices()
        logging.info("Starting discovery...")
        self.manager.start_discovery()

        while discovering:
            time.sleep(1)
            logging.info("Devices found: %s", len(self.manager.devices()))
            for dev in self.manager.devices():
                if dev.mac_address == self.mac_address or dev.alias() == self.alias:
                    logging.info(
                        "Found bt1 device %s  [%s]", dev.alias(), dev.mac_address
                    )
                    discovering = False
                    found = True
            wait = wait - 1
            if wait <= 0:
                discovering = False
        self.manager.stop_discovery()

        if found:
            self._connect()
        else:
            logging.error(
                "Device not found: [%s], please check the details provided.",
                self.mac_address,
            )
            self.gracefully_exit(True)

    def _connect(self):
        try:
            self.device.connect()
            self.manager.run()
        except Exception as e:
            logging.error(e)
            self.gracefully_exit(True)
        except KeyboardInterrupt:
            self.gracefully_exit()

    def on_resolved(self):
        logging.debug("resolved services")

    def on_data_received(self, value):
        logging.debug("junctek data received!")
        bs = str(value.hex()).upper()
        logging.debug(bs)
        if not validate(bs):
            return False

        data = parse_incoming_bytestream(bs, self.battery_capacity_ah, self.charging)
        for key in data:
            self.data[key] = data[key]

        if self.data_callback is not None:
            self.data_callback(self.data)

        if self.continuous and self.interval > 0:
            logging.info("Query Junctek again in {} seconds...".format(self.interval))
            time.sleep(self.interval)
            self.request_data()

    def gracefully_exit(self, connectFailed=False):
        logging.info("gracefully_exit")
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        if self.device is not None and not connectFailed and self.device.is_connected():
            logging.info(
                "Exit: Disconnecting device: %s [%s]",
                self.device.alias(),
                self.device.mac_address,
            )
            self.device.disconnect()
        self.manager.stop()
        os._exit(os.EX_OK)
