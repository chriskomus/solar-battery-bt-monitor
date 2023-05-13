#!/usr/bin/env python3

# ------------------------------------------------------
# Original Author: Scott Nichol
# https://github.com/snichol67/solar-bt-monitor

# Modifications by: Chris Komus
#
# Sets up logging, reads the configuration file, and
# attempts to connect to the bluetooth module. If
# continuous monitoring is set, the BTOneApp has been
# modified to sleep for 30 seconds, then request
# another data read from the BT-1 device
#
# If auto_reconnect is set, if the bluetooth connection
# initially fails (and it often does), the script
# sleeps for 10 seconds and tries to reconnect again.
#
# Feel free to reuse this code for any purpose
# ------------------------------------------------------

import logging
import configparser

from lib import dual_log
from lib.bt_one.bt_one_app import BTOneApp
from lib.junctek.junctek_app import JunctekApp

# Read configuration file
config = configparser.ConfigParser()
config.read("solar-battery-bt-monitor.ini")

# Set logging level
log_level = config.get("monitor", "log_level", fallback="INFO")
if log_level is None or log_level == "INFO":
    level = logging.INFO
elif log_level == "DEBUG":
    level = logging.DEBUG
elif log_level == "WARN":
    level = logging.WARN
elif log_level == "ERROR":
    level = logging.ERROR

dual_log.setup(
    "solar-battery-bt-monitor",
    minLevel=level,
    fileLevel=level,
    rotation="daily",
    keep=30,
)

adapter = config.get("monitor", "adapter", fallback=None)
logging.debug("[CONFIG] adapter: {}".format(adapter))

reconnect = config.getboolean("monitor", "reconnect", fallback=False)
logging.debug("[CONFIG] reconnect: {}".format(reconnect))


# Renogy BT-1
renogy_enabled = config.getboolean("renogy", "enabled", fallback=False)
logging.debug("[CONFIG] renogy_enabled: {}".format(renogy_enabled))

renogy_mac_addr = config.get("renogy", "mac_addr", fallback=None)
logging.debug("[CONFIG] renogy_mac_addr: {}".format(renogy_mac_addr))

renogy_alias = config.get("renogy", "device_alias", fallback=None)
logging.debug("[CONFIG] renogy_alias: {}".format(renogy_alias))

renogy_continuous = config.getboolean("renogy", "continuous_monitor", fallback=False)
logging.debug("[CONFIG] continuous_monitor: {}".format(renogy_continuous))

renogy_interval = -1
if renogy_continuous:
    renogy_interval = config.getint("renogy", "data_read_interval", fallback=-1)
    logging.debug("[CONFIG] data_read_interval: {}".format(renogy_interval))

# Junctek KH140F
junctek_enabled = config.getboolean("junctek", "enabled", fallback=False)
logging.debug("[CONFIG] junctek_enabled: {}".format(junctek_enabled))

junctek_mac_addr = config.get("junctek", "mac_addr", fallback=None)
logging.debug("[CONFIG] junctek_mac_addr: {}".format(junctek_mac_addr))

junctek_alias = config.get("junctek", "device_alias", fallback=None)
logging.debug("[CONFIG] junctek_alias: {}".format(junctek_alias))

junctek_continuous = config.getboolean("junctek", "continuous_monitor", fallback=False)
logging.debug("[CONFIG] junctek_continuous_monitor: {}".format(junctek_continuous))

junctek_interval = -1
if junctek_continuous:
    junctek_interval = config.getint("junctek", "data_read_interval", fallback=-1)
    logging.debug("[CONFIG] junctek_data_read_interval: {}".format(junctek_interval))

junctek_battery_capacity_ah = config.getint("junctek", "battery_capacity_ah", fallback=100)
logging.debug(
    "[CONFIG] junctek_battery_capacity_ah: {}".format(junctek_battery_capacity_ah)
)

junctek_start_script_as_charging = config.getboolean(
    "junctek", "start_script_as_charging", fallback=False
)
logging.debug(
    "[CONFIG] junctek_start_script_as_charging: {}".format(
        junctek_start_script_as_charging
    )
)

# Logging
logger_type = config.get("monitor", "data_logger", fallback="prometheus")
logging.debug("[CONFIG] logger_type: {}".format(logger_type))

# Connect to BT-1 and Junctek
if renogy_mac_addr is None:
    logging.error(
        "No configuration item for renogy_mac_addr. This configuration item is required."
    )
elif renogy_alias is None:
    logging.error(
        "No configuration item for renogy_device_alias.  This configuration item is required."
    )
elif adapter is None:
    logging.error(
        "No configuration item for adapter.  This configuration item is required."
    )
else:
    data_logger = None
    if logger_type == "prometheus":
        from lib.prometheus_logger import prometheus_logger

        data_logger = prometheus_logger()

    if data_logger is not None:
        if renogy_enabled:
            bt1 = BTOneApp(
                adapter_name=adapter,
                mac_address=renogy_mac_addr,
                alias=renogy_alias,
                on_data_received=data_logger.data_received_callback,
                auto_reconnect=reconnect,
                continuous=renogy_continuous,
                interval=renogy_interval,
            )
            bt1.connect()

        if junctek_enabled:
            junctek = JunctekApp(
                adapter_name=adapter,
                mac_address=junctek_mac_addr,
                alias=junctek_alias,
                on_data_received=data_logger.data_received_callback,
                auto_reconnect=reconnect,
                continuous=junctek_continuous,
                interval=junctek_interval,
                battery_capacity_ah=junctek_battery_capacity_ah,
                start_script_as_charging=junctek_start_script_as_charging,
            )
            junctek.connect()
