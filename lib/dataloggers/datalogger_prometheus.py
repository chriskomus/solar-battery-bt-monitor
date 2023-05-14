# ------------------------------------------------------
# Original Author: Scott Nichol
# https://github.com/snichol67/solar-bt-monitor
#
# Modifications by: Chris Komus
#
# This small module sets up several prometheus gauges
# and starts the prometheus server on port 5000.  The
# prometheus_logger class provides a method that is
# used as a callback for when data is received by the
# bluetooth modules.
#
# When data is received, we set a value on each of the
# mapped gauges, pushing them into the prometheus store.
#
# Feel free to reuse this code for any purpose
# ------------------------------------------------------
import logging
import psutil

from gpiozero import CPUTemperature
from prometheus_client import start_http_server, Gauge

prometheus_map = {
    "function": Gauge("solarmon_function", "Function"),
    "battery_percentage": Gauge("solarmon_battery_percentage", "Battery %"),
    "battery_voltage": Gauge("solarmon_battery_volts", "Battery Voltage"),
    "battery_current": Gauge("solarmon_battery_current", "Battery Current"),
    "battery_temperature": Gauge(
        "solarmon_battery_temperature_celsius", "Battery Temperature"
    ),
    "controller_temperature": Gauge(
        "solarmon_controller_temperature_celsius", "Controller Temperature"
    ),
    "load_status": Gauge("solarmon_load_status", "Load Status"),
    "load_voltage": Gauge("solarmon_load_volts", "Load Voltage"),
    "load_current": Gauge("solarmon_load_amperes", "Load Current"),
    "load_power": Gauge("solarmon_load_power_watts", "Load Power"),
    "pv_voltage": Gauge("solarmon_solar_volts", "Solar Voltage"),
    "pv_current": Gauge("solarmon_solar_amperes", "Solar Current"),
    "pv_power": Gauge("solarmon_solar_watts", "Solar Power"),
    "max_charging_power_today": Gauge(
        "solarmon_max_charging_power_today", "Max Charging Power Today"
    ),
    "max_discharging_power_today": Gauge(
        "solarmon_max_discharging_power_today", "Max Discharging Power Today"
    ),
    "charging_amp_hours_today": Gauge(
        "solarmon_charging_amp_hours_today", "Charging Amp Hours Today"
    ),
    "discharging_amp_hours_today": Gauge(
        "solarmon_discharging_amp_hours_today", "Discharging Amp Hours Today"
    ),
    "power_generation_today": Gauge(
        "solarmon_power_generation_today", "Power Generation Today"
    ),
    "power_consumption_today": Gauge(
        "solarmon_power_consumption_today", "Power Consumption Today"
    ),
    "power_generation_total": Gauge(
        "solarmon_power_generation_total", "Power Generation Total"
    ),
    "charging_status": Gauge("solarmon_controller_charging_state", "Charging Status"),
    "junctek_load_status": Gauge("junctek_load_status", "Load Status"),
    "junctek_load_volts": Gauge("junctek_load_volts", "Load Voltage"),
    "junctek_load_amps": Gauge("junctek_load_amps", "Load Current"),
    "junctek_load_power_watts": Gauge("junctek_load_power_watts", "Load Power"),
    "junctek_battery_percentage": Gauge("junctek_battery_percentage", "Battery %"),
    "junctek_temp": Gauge("junctek_temp", "Temperature"),
    "junctek_ah_remaining": Gauge("junctek_ah_remaining", "Amp Hours Remaining"),
    "junctek_min_remaining": Gauge("junctek_min_remaining", "Minutes Remaining"),
    "junctek_max_capacity": Gauge("junctek_max_capacity", "Max Battery Capacity"),
    "pi_temp": Gauge("pi_temperature_celcius", "Pi Temperature"),
    "pi_cpu": Gauge("pi_cpu_usage", "Pi CPU Usage"),
    "pi_ram": Gauge("pi_ram_usage", "Pi RAM Usage"),
    "pi_storage": Gauge("pi_storage_usage", "Pi Storage Usage"),
}


class PrometheusLogger:
    def __init__(self):
        logging.info("Starting Prometheus Server")
        start_http_server(5000)

    def data_received_callback(self, data):
        """
        Combine pi stats with the incoming data and set prometheus guages
        """
        try:
            combined_data = {**data, **self.pi_stats()}

            for key in combined_data:
                value = combined_data[key]
                gauge = prometheus_map[key]
                gauge.set(value)
                logging.info("{}: {}".format(key, value))

            return True
        except Exception as e:
            logging.warning("{}".format(e))
            return False

    def pi_stats(self):
        """
        Append pi stats after receiving data from BT-1 or Junctek
        """
        return {
            "pi_temp": CPUTemperature().temperature,
            "pi_cpu": psutil.cpu_percent(),
            "pi_ram": psutil.virtual_memory().percent,
            "pi_storage": psutil.disk_usage("/").percent,
        }
