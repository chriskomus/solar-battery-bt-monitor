# ------------------------------------------------------
# Modifications by: Chris Komus
#
# Original Authors: Olen
# https://github.com/Olen/solar-monitor
#
# If continuous monitoring is set, the device will poll
# for data and sleep for x seconds, then request
# another data read from the device.
#
# If auto_reconnect is set, if the bluetooth connection
# initially fails (and it often does), the script
# sleeps for 10 seconds and tries to reconnect again.
#
# Feel free to reuse this code for any purpose
# ------------------------------------------------------

import gatt
import logging
import time
import threading
import importlib
from datetime import datetime, timedelta
import psutil
from gpiozero import CPUTemperature

# from lib.devices.battery_device import BatteryDevice
# from lib.devices.charge_controller_device import ChargeControllerDevice
# from lib.devices.inverter_device import InverterDevice
# from lib.devices.monitoring_device import MonitoringDevice
# from lib.devices.power_device import PowerDevice
# from lib.devices.rectifier_device import RectifierDevice


class SolarDeviceManager(gatt.DeviceManager):
    def __init__(self, adapter_name):
        super().__init__(adapter_name)

    def device_discovered(self, device):
        logging.info(
            "[{}] Discovered, alias = {}".format(device.mac_address, device.alias())
        )

    def make_device(self, mac_address):
        return SolarDevice(mac_address=mac_address, manager=self)


class SolarDevice(gatt.Device):
    def __init__(
        self,
        mac_address,
        manager,
        logger_name="unknown",
        datalogger=None,
        config=None,
    ):
        super().__init__(mac_address=mac_address, manager=manager)
        self.logger_name = logger_name
        self.service_notify = None
        self.service_write = None
        self.char_notify = None
        self.char_write = None
        self.device_id = None
        self.send_ack = None
        self.need_polling = None
        self.wait_to_send = None
        self.util = None
        self.device_type = None
        self.module = None
        self.device_write_characteristic_polling = None
        self.device_write_characteristic_commands = None
        self.datalogger = datalogger
        self.run_device_poller = False
        self.poller_thread = None
        self.run_command_poller = False
        self.command_thread = None
        self.command_trigger = None
        self.config = config
        self.time_of_last_send = None
        self.time_of_last_pi_stat_send = None

        # old
        # self.data_callback = on_data
        # self.resolved_callback = on_resolved

        if self.config:
            self.auto_reconnect = self.config.getboolean(
                "monitor", "reconnect", fallback=False
            )
            self.data_read_interval = self.config.getint(
                logger_name, "data_read_interval", fallback=30
            )
            self.data_send_interval = self.config.getint(
                logger_name, "data_send_interval", fallback=0
            )
            self.device_type = self.config.get(
                logger_name, "device_type", fallback=None
            )
            self.round_digits = self.config.getint(
                logger_name, "round_digits", fallback=1
            )
        self.writing = False

        if not self.device_type:
            return

        try:
            self.module = importlib.import_module("lib.plugins." + self.device_type)
            logging.info("Successfully imported {}.".format(self.device_type))
        except ImportError:
            logging.error("Error importing {}".format(self.device_type))
            raise ImportError()

        self.service_notify = getattr(self.module.Config, "NOTIFY_SERVICE_UUID", None)
        self.service_write = getattr(self.module.Config, "WRITE_SERVICE_UUID", None)
        self.char_notify = getattr(self.module.Config, "NOTIFY_CHAR_UUID", None)
        self.char_write_polling = getattr(
            self.module.Config, "WRITE_CHAR_UUID_POLLING", None
        )
        self.char_write_commands = getattr(
            self.module.Config, "WRITE_CHAR_UUID_COMMANDS", None
        )
        self.device_id = getattr(self.module.Config, "DEVICE_ID", None)
        self.need_polling = getattr(self.module.Config, "NEED_POLLING", None)
        self.wait_to_send = getattr(self.module.Config, "WAIT_TO_SEND", None)
        self.send_ack = getattr(self.module.Config, "SEND_ACK", None)

        # this will be sent to the datalogger
        self.data_payload = {}

        # if "battery" in self.logger_name:
        #     self.entities = BatteryDevice(parent=self)
        # elif "controller" in self.logger_name:
        #     self.entities = ChargeControllerDevice(parent=self)
        # elif "inverter" in self.logger_name:
        #     self.entities = InverterDevice(parent=self)
        # elif "rectifier" in self.logger_name:
        #     self.entities = RectifierDevice(parent=self)
        # elif "monitoring" in self.logger_name:
        #     self.entities = MonitoringDevice(parent=self)
        # else:
        #     self.entities = PowerDevice(parent=self)

    def alias(self):
        alias = super().alias()
        if alias:
            return alias.strip()
        return None

    def connect(self):
        logging.info("[{}] Connecting to {}".format(self.logger_name, self.mac_address))
        super().connect()

    def connect_succeeded(self):
        super().connect_succeeded()
        logging.info("[{}] Connected to {}".format(self.logger_name, self.alias()))

    def connect_failed(self, error):
        super().connect_failed(error)
        logging.info("[{}] Connection failed: {}".format(self.logger_name, str(error)))
        if self.poller_thread:
            self.run_device_poller = False
            logging.info("[{}] Stopping poller-thread".format(self.logger_name))
        if self.command_thread:
            logging.info("[{}] Stopping command-thread".format(self.logger_name))
            self.run_command_poller = False
            self.command_trigger.set()
        if self.auto_reconnect:
            logging.info("[{}] Reconnecting in 10 seconds".format(self.logger_name))
            time.sleep(10)
            self.connect()

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logging.info("[{}] Disconnected".format(self.logger_name))
        if self.poller_thread:
            self.run_device_poller = False
            logging.info("[{}] Stopping poller-thread".format(self.logger_name))
        if self.command_thread:
            logging.info("[{}] Stopping command-thread".format(self.logger_name))
            self.run_command_poller = False
            self.command_trigger.set()
        if self.auto_reconnect:
            logging.info("[{}] Reconnecting in 10 seconds".format(self.logger_name))
            time.sleep(10)
            self.connect()

    def services_resolved(self):
        super().services_resolved()
        logging.info("[{}] Connected to {}".format(self.logger_name, self.alias()))
        logging.info("[{}] Resolved services".format(self.logger_name))

        if self.config:
            self.util = self.module.Util(
                logger_name=self.logger_name, config=self.config
            )
        else:
            raise ValueError("[{}] Missing config".format(self.logger_name))

        device_notification_service = None
        device_write_service = None
        for service in self.services:
            logging.info("[{}]  Service [{}]".format(self.logger_name, service.uuid))
            if self.service_notify and service.uuid == self.service_notify:
                logging.info(
                    "[{}]  - Found dev notify service [{}]".format(
                        self.logger_name, service.uuid
                    )
                )
                device_notification_service = service
            if self.service_write and service.uuid == self.service_write:
                logging.info(
                    "[{}]  - Found dev write service [{}]".format(
                        self.logger_name, service.uuid
                    )
                )
                device_write_service = service
            for characteristic in service.characteristics:
                logging.info(
                    "[{}]    Characteristic [{}]".format(
                        self.logger_name, characteristic.uuid
                    )
                )

        if device_notification_service:
            for c in device_notification_service.characteristics:
                if self.char_notify and c.uuid in self.char_notify:
                    logging.info(
                        "[{}] Found dev notify char [{}]".format(
                            self.logger_name, c.uuid
                        )
                    )
                    logging.info(
                        "[{}] Subscribing to notify char [{}]".format(
                            self.logger_name, c.uuid
                        )
                    )
                    c.enable_notifications()
        if device_write_service:
            for c in device_write_service.characteristics:
                if self.char_write_polling and c.uuid == self.char_write_polling:
                    logging.info(
                        "[{}] Found dev write polling char [{}]".format(
                            self.logger_name, c.uuid
                        )
                    )
                    self.device_write_characteristic_polling = c
                if self.char_write_commands and c.uuid == self.char_write_commands:
                    logging.info(
                        "[{}] Found dev write polling char [{}]".format(
                            self.logger_name, c.uuid
                        )
                    )
                    self.device_write_characteristic_commands = c

        if self.need_polling:
            self.poller_thread = threading.Thread(target=self.device_poller)
            self.poller_thread.daemon = True
            self.poller_thread.name = "Device-poller-thread {}".format(self.logger_name)
            self.poller_thread.start()

        # We only need an MQTT-poller thread if we have a write characteristic to send data to and MQTT is set up
        if self.char_write_commands and self.datalogger.mqtt is not None:
            self.command_trigger = threading.Event()
            self.datalogger.mqtt.trigger[self.logger_name] = self.command_trigger
            self.command_thread = threading.Thread(
                target=self.mqtt_poller, args=(self.command_trigger,)
            )
            self.command_thread.daemon = True
            self.command_thread.name = "MQTT-poller-thread {}".format(self.logger_name)
            self.command_thread.start()

    def descriptor_read_value_failed(self, descriptor, error):
        logging.warn("descriptor_value_failed")

    def characteristic_value_updated(self, characteristic, value):
        super().characteristic_value_updated(characteristic, value)

        data = self.util.on_data_received(value)

        if data:
            if self.send_ack:
                ack_data = self.util.ack_data(value)
                self.characteristic_write_value(
                    ack_data, self.device_write_characteristic_polling
                )

            self.send_data_to_logger(data)

            if self.need_polling:
                logging.debug(
                    "[{}] Query again in {} seconds...".format(
                        self.logger_name, self.data_read_interval
                    )
                )

    def characteristic_enable_notifications_succeeded(self, characteristic):
        super().characteristic_enable_notifications_succeeded(characteristic)
        logging.info(
            "[{}] Notifications enabled for: [{}]".format(
                self.logger_name, characteristic.uuid
            )
        )

    def characteristic_enable_notifications_failed(self, characteristic, error):
        super().characteristic_enable_notifications_failed(characteristic, error)
        logging.warning(
            "[{}] Enabling notifications failed for: [{}] with error [{}]".format(
                self.logger_name, characteristic.uuid, str(error)
            )
        )

    def characteristic_write_value(self, value, write_characteristic):
        logging.debug(
            "[{}] Writing data to {} - {} ({})".format(
                self.logger_name,
                write_characteristic.uuid,
                value,
                bytearray(value).hex(),
            )
        )
        self.writing = value
        write_characteristic.write_value(value)

    def characteristic_write_value_succeeded(self, characteristic):
        super().characteristic_write_value_succeeded(characteristic)
        logging.debug(
            "[{}] Write to characteristic done for: [{}]".format(
                self.logger_name, characteristic.uuid
            )
        )
        self.writing = False

    def characteristic_write_value_failed(self, characteristic, error):
        super().characteristic_write_value_failed(characteristic, error)
        logging.warning(
            "[{}] Write to characteristic failed for: [{}] with error [{}]".format(
                self.logger_name, characteristic.uuid, str(error)
            )
        )
        if error == "In Progress" and self.writing is not False:
            time.sleep(0.1)
            self.characteristic_write_value(self.writing, characteristic)
        else:
            self.writing = False

    # Pollers
    # Implement polling in separate threads to be able to
    # sleep without blocking notifications

    def device_poller(self):
        # Loop every x seconds (set by self.data_read_interval)
        # the device plugin is responsible for not overloading the device with requests
        logging.info(
            "[{}] Starting new thread {}".format(
                self.logger_name, threading.current_thread().name
            )
        )
        self.run_device_poller = True
        while self.run_device_poller:
            logging.debug(
                "[{}] Looping thread {}".format(
                    self.logger_name, threading.current_thread().name
                )
            )
            payload = self.util.poll_request()
            if payload:
                self.characteristic_write_value(
                    payload, self.device_write_characteristic_polling
                )
            time.sleep(self.data_read_interval)
        logging.info(
            "[{}] Ending thread {}".format(
                self.logger_name, threading.current_thread().name
            )
        )

    def mqtt_poller(self, trigger):
        # Loop to fetch MQTT-commands
        logging.info(
            "[{}] Starting new thread {}".format(
                self.logger_name, threading.current_thread().name
            )
        )
        self.run_command_poller = True
        while self.run_command_poller:
            mqtt_sets = []
            datas = []
            logging.info(
                "[{}] {} Waiting for event...".format(
                    self.logger_name, threading.current_thread().name
                )
            )
            trigger.wait()
            logging.info(
                "[{}] {} Event happened...".format(
                    self.logger_name, threading.current_thread().name
                )
            )
            trigger.clear()
            try:
                mqtt_sets = self.datalogger.mqtt.sets[self.logger_name]
                self.datalogger.mqtt.sets[self.logger_name] = []
            except Exception as e:
                logging.error(
                    "[{}] {} Something bad happened: {}".format(
                        self.logger_name, threading.current_thread().name, e
                    )
                )
                pass
            for msg in mqtt_sets:
                var = msg[0]
                message = msg[1]
                logging.info(
                    "[{}] MQTT-msg: {} -> {}".format(self.logger_name, var, message)
                )
                datas = self.util.cmdRequest(var, message)
                if len(datas) > 0:
                    for data in datas:
                        logging.debug(
                            "[{}] Sending data to device: {}".format(
                                self.logger_name, data
                            )
                        )
                        self.characteristic_write_value(
                            data, self.device_write_characteristic_commands
                        )
                        time.sleep(0.2)
                else:
                    logging.debug(
                        "[{}] Unknown MQTT-command {} -> {}".format(
                            self.logger_name, var, message
                        )
                    )
                logging.info("[{}] MQTT msq complete".format(self.logger_name))
        logging.info(
            "[{}] Ending thread {}".format(
                self.logger_name, threading.current_thread().name
            )
        )

    def send_data_to_logger(self, data):
        """
        Log data changes continously for url and mqtt logging, and log
        periodically for prometheus (set by self.data_send_interval).

        Periodically append updating pi stats.
        """
        # combine existing payload with new payload, this prevents skipped
        # data if its not time to send a new payload to datalogger
        self.data_payload = {**self.data_payload, **data}

        # append pi stats (cpu, ram, hd, temp)
        # data = self.append_pi_stats(data)
        self.append_pi_stats()

        for key, value in self.data_payload.items():
            # universally round all numbers
            if isinstance(value, int) or isinstance(value, float):
                self.data_payload[key] = round(value, self.round_digits)

            self.datalogger.log(self.logger_name, key, self.data_payload[key])

        is_resend_ready = False
        if self.time_of_last_send:
            is_resend_ready = self.time_of_last_send < datetime.now() - timedelta(
                seconds=self.data_send_interval
            )

        # if not self.wait_to_send or self.time_of_last_send is None or (time_since_last_send > self.data_send_interval):
        if not self.wait_to_send or self.time_of_last_send is None or is_resend_ready:
            if self.datalogger.log_to_prometheus(self.data_payload):
                self.time_of_last_send = datetime.now()

                if self.wait_to_send:
                    logging.debug(
                        "[{}] Logged to Prometheus. Sending again in {} seconds...".format(
                            self.logger_name, self.data_send_interval
                        )
                    )

        # logging.info(
        #     "[{}] Starting new thread {}".format(
        #         self.logger_name, threading.current_thread().name
        #     )
        # )
        # self.run_device_poller = True
        # while self.run_device_poller:
        #     logging.debug(
        #         "[{}] Looping thread {}".format(
        #             self.logger_name, threading.current_thread().name
        #         )
        #     )
        #     payload = self.util.poll_request()
        #     if payload:
        #         self.characteristic_write_value(
        #             payload, self.device_write_characteristic_polling
        #         )
        #     time.sleep(self.data_read_interval)
        # logging.info(
        #     "[{}] Ending thread {}".format(
        #         self.logger_name, threading.current_thread().name
        #     )
        # )

    def append_pi_stats(self):
        # def append_pi_stats(self, data):
        """
        Append pi stats
        """
        is_pi_append_ready = False
        if self.time_of_last_pi_stat_send:
            is_pi_append_ready = (
                self.time_of_last_pi_stat_send < datetime.now() - timedelta(seconds=30)
            )

        if self.time_of_last_pi_stat_send is None or is_pi_append_ready:
            pi_stats = {
                "pi_temp": round(CPUTemperature().temperature),
                "pi_cpu": round(psutil.cpu_percent()),
                "pi_ram": round(psutil.virtual_memory().percent),
                "pi_storage": round(psutil.disk_usage("/").percent),
            }

            self.time_of_last_pi_stat_send = datetime.now()

            self.data_payload = {**self.data_payload, **pi_stats}

        # return data
