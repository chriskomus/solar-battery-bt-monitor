# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Olen
# https://github.com/Olen/solar-monitor
#
# ------------------------------------------------------
from datetime import datetime, timedelta
import logging
import requests

from lib.dataloggers.datalogger_mqtt import DataLoggerMqtt


class DataLogger:
    def __init__(self, config):
        # config.get('datalogger', 'url'), config.get('datalogger', 'token')
        logging.debug("Creating new DataLogger")

        logger_type = config.get("monitor", "data_logger", fallback="prometheus")
        logging.debug("[CONFIG] logger_type: {}".format(logger_type))

        self.url = None
        self.mqtt = None
        self.prometheus_logger = None

        if config.getboolean("datalogger", "log_to_prometheus", fallback=False):
            from lib.dataloggers.datalogger_prometheus import PrometheusLogger

            self.prometheus_logger = PrometheusLogger()
        if config.getboolean("datalogger", "log_to_url", fallback=False) and config.get(
            "datalogger", "url", fallback=None
        ):
            self.url = config.get("datalogger", "url")
            self.token = config.get("datalogger", "token")
        if config.getboolean(
            "datalogger", "log_to_mqtt", fallback=False
        ) and config.get("mqtt", "broker", fallback=None):
            self.mqtt = DataLoggerMqtt(
                config.get("mqtt", "broker"),
                1883,
                prefix=config.get("mqtt", "prefix"),
                username=config.get("mqtt", "username"),
                password=config.get("mqtt", "password"),
                hostname=config.get("mqtt", "hostname"),
            )
        self.logdata = {}

    def log(self, device, var, val):
        if self.url or self.mqtt:
            # MQTT and URL - Only log modified data
            # <timestamp> <device> <var>: <val>
            device = device.strip()
            # ts = datetime.now().isoformat(' ', 'seconds')
            ts = datetime.now()
            if device not in self.logdata:
                self.logdata[device] = {}
            if var not in self.logdata[device]:
                self.logdata[device][var] = {}
                self.logdata[device][var]["ts"] = None
                self.logdata[device][var]["value"] = None

            if self.logdata[device][var]["value"] != val:
                self.logdata[device][var]["ts"] = ts
                self.logdata[device][var]["value"] = val
                logging.info("[{}] Sending new data {}: {}".format(device, var, val))
                self.send_to_server(device, var, val)
            elif self.logdata[device][var]["ts"] < datetime.now() - timedelta(
                minutes=15
            ):
                self.logdata[device][var]["ts"] = ts
                self.logdata[device][var]["value"] = val
                logging.info(
                    "[{}] Sending refreshed data {}: {}".format(device, var, val)
                )
                self.send_to_server(device, var, val)

    def send_to_server(self, device, var, val):
        if self.mqtt:
            self.mqtt.publish(device, var, val)
        if self.url:
            # logging.info("[{}] Sending data to {}".format(device, self.url))
            ts = datetime.now().isoformat(" ", "seconds")
            payload = {"device": device, var: val, "ts": ts}
            header = {
                "Content-type": "application/json",
                "Accept": "text/plain",
                "Authorization": "Bearer {}".format(self.token),
            }
            try:
                response = requests.post(url=self.url, json=payload, headers=header)
            except TimeoutError:
                logging.error("Connection to {} timed out!".format(self.url))

    def log_to_prometheus(self, values):
        """
        Unlike url and mqtt, we want to send the entire set of data to Prometheus

        This should be called on intervals, not every time there is an update.
        """
        if self.prometheus_logger:
            return self.prometheus_logger.data_received_callback(values)
        return False
