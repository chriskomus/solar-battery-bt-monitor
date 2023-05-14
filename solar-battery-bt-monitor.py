#!/usr/bin/env python3

# ------------------------------------------------------
# Modifications by: Chris Komus
# Original Author: Scott Nichol, Olen, Cyril Sebastian
#
# Sets up logging, reads the configuration file, and
# attempts to connect to the bluetooth modules.
#
# Feel free to reuse this code for any purpose
# ------------------------------------------------------
import os
import logging
import time
import configparser

from lib import dual_log
from lib.solar_device import SolarDeviceManager, SolarDevice
from lib.plugins.Renogy import Util as BTOneApp
from lib.plugins.Junctek import Util as JunctekApp
from lib.dataloggers.datalogger import DataLogger

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

# Set up dual logging
dual_log.setup(
    "solar-battery-bt-monitor",
    minLevel=level,
    fileLevel=level,
    rotation="daily",
    keep=30,
)

# Set up data logger type
datalogger = DataLogger(config)

# General Config
adapter = config.get("monitor", "adapter", fallback=None)
logging.debug("[CONFIG] adapter: {}".format(adapter))

reconnect = config.getboolean("monitor", "reconnect", fallback=False)
logging.debug("[CONFIG] reconnect: {}".format(reconnect))


# Set up device manager and adapter
device_manager = SolarDeviceManager(adapter_name=config["monitor"]["adapter"])
logging.info("Adapter status - Powered: {}".format(device_manager.is_adapter_powered))
if not device_manager.is_adapter_powered:
    logging.info("Powering on the adapter ...")
    device_manager.is_adapter_powered = True
    logging.info("Powered on")

# Run discovery
device_manager.update_devices()
logging.info("Starting discovery...")
# scan all the advertisements from the services list
device_manager.start_discovery()
discovering = True
wait = 15
found = []
# delay / sleep for 10 ~ 15 sec to complete the scanning
while discovering:
    time.sleep(1)
    f = len(device_manager.devices())
    logging.debug("Found {} BLE-devices so far".format(f))
    found.append(f)
    if len(found) > 5:
        if found[len(found) - 5] == f:
            # We did not find any new devices the last 5 seconds
            discovering = False
    wait = wait - 1
    if wait == 0:
        discovering = False

device_manager.stop_discovery()
logging.info("Found {} BLE-devices".format(len(device_manager.devices())))


for dev in device_manager.devices():
    logging.debug("Scanning device {} {}".format(dev.mac_address, dev.alias()))
    for section in config.sections():
        mac_address = config.get(section, "mac_address", fallback=None)
        device_type = config.get(section, "device_type", fallback=None)
        enabled = config.getboolean(section, "enabled", fallback=False)

        if enabled and mac_address and device_type:
            # mac = config.get(section, "mac_address").lower()
            if dev.mac_address.lower() == mac_address.lower():
                logging.info("Trying to connect to {}...".format(dev.mac_address))
                try:
                    device = SolarDevice(
                        mac_address=dev.mac_address,
                        manager=device_manager,
                        logger_name=section,
                        datalogger=datalogger,
                        config=config,
                    )
                except Exception as e:
                    logging.error(e)
                    continue
                logging.debug("Connected")
                device.connect()
logging.info("Nothing to process. Terminate with Ctrl+C")
try:
    device_manager.run()
except KeyboardInterrupt:
    pass

for dev in device_manager.devices():
    device.disconnect()


# # Renogy BT-1
# renogy_enabled = config.getboolean("renogy", "enabled", fallback=False)
# logging.debug("[CONFIG] renogy_enabled: {}".format(renogy_enabled))

# renogy_mac_addr = config.get("renogy", "mac_address", fallback=None)
# logging.debug("[CONFIG] renogy_mac_addr: {}".format(renogy_mac_addr))

# renogy_alias = config.get("renogy", "device_alias", fallback=None)
# logging.debug("[CONFIG] renogy_alias: {}".format(renogy_alias))

# renogy_continuous = config.getboolean("renogy", "continuous_monitor", fallback=False)
# logging.debug("[CONFIG] continuous_monitor: {}".format(renogy_continuous))

# renogy_interval = -1
# if renogy_continuous:
#     renogy_interval = config.getint("renogy", "data_read_interval", fallback=-1)
#     logging.debug("[CONFIG] data_read_interval: {}".format(renogy_interval))

# # Junctek KH140F
# junctek_enabled = config.getboolean("junctek", "enabled", fallback=False)
# logging.debug("[CONFIG] junctek_enabled: {}".format(junctek_enabled))

# junctek_mac_addr = config.get("junctek", "mac_address", fallback=None)
# logging.debug("[CONFIG] junctek_mac_addr: {}".format(junctek_mac_addr))

# junctek_alias = config.get("junctek", "device_alias", fallback=None)
# logging.debug("[CONFIG] junctek_alias: {}".format(junctek_alias))

# junctek_continuous = config.getboolean("junctek", "continuous_monitor", fallback=False)
# logging.debug("[CONFIG] junctek_continuous_monitor: {}".format(junctek_continuous))

# junctek_interval = -1
# if junctek_continuous:
#     junctek_interval = config.getint("junctek", "data_read_interval", fallback=-1)
#     logging.debug("[CONFIG] junctek_data_read_interval: {}".format(junctek_interval))

# junctek_battery_capacity_ah = config.getint("junctek", "battery_capacity_ah", fallback=100)
# logging.debug(
#     "[CONFIG] junctek_battery_capacity_ah: {}".format(junctek_battery_capacity_ah)
# )

# junctek_start_script_as_charging = config.getboolean(
#     "junctek", "start_script_as_charging", fallback=False
# )
# logging.debug(
#     "[CONFIG] junctek_start_script_as_charging: {}".format(
#         junctek_start_script_as_charging
#     )
# )


# # Connect to BT-1 and Junctek
# if renogy_mac_addr is None:
#     logging.error(
#         "No configuration item for renogy_mac_addr. This configuration item is required."
#     )
# elif renogy_alias is None:
#     logging.error(
#         "No configuration item for renogy_device_alias.  This configuration item is required."
#     )
# elif adapter is None:
#     logging.error(
#         "No configuration item for adapter.  This configuration item is required."
#     )
# else:
#     data_logger = None
#     if logger_type == "prometheus":
#         from lib.prometheus_logger import prometheus_logger

#         data_logger = prometheus_logger()

#     if data_logger is not None:
#         if renogy_enabled:
#             bt1 = BTOneApp(
#                 adapter_name=adapter,
#                 mac_address=renogy_mac_addr,
#                 alias=renogy_alias,
#                 on_data_received=data_logger.data_received_callback,
#                 auto_reconnect=reconnect,
#                 continuous=renogy_continuous,
#                 interval=renogy_interval,
#                 config=config
#             )
#             bt1.connect()

#         if junctek_enabled:
#             junctek = JunctekApp(
#                 adapter_name=adapter,
#                 mac_address=junctek_mac_addr,
#                 alias=junctek_alias,
#                 on_data_received=data_logger.data_received_callback,
#                 auto_reconnect=reconnect,
#                 continuous=junctek_continuous,
#                 interval=junctek_interval,
#                 battery_capacity_ah=junctek_battery_capacity_ah,
#                 start_script_as_charging=junctek_start_script_as_charging,
#                 config=config
#             )
#             junctek.connect()
