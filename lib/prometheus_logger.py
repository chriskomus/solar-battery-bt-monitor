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
from prometheus_client import start_http_server, Gauge
import logging
from gpiozero import CPUTemperature
import psutil

prometheus_map = {
    'function': Gauge('solarmon_function', 'Function'),
    'battery_percentage': Gauge('solarmon_battery_percentage', 'Battery %'),
    'battery_voltage': Gauge('solarmon_battery_volts', 'Battery Voltage'),
    'battery_current': Gauge('solarmon_battery_current', 'Battery Current'),
    'battery_temperature': Gauge('solarmon_battery_temperature_celsius', 'Battery Temperature'),
    'controller_temperature': Gauge('solarmon_controller_temperature_celsius', 'Controller Temperature'),
    'load_status': Gauge('solarmon_load_status', 'Load Status'),
    'load_voltage': Gauge('solarmon_load_volts', 'Load Voltage'),
    'load_current': Gauge('solarmon_load_amperes', 'Load Current'),
    'load_power': Gauge('solarmon_load_power_watts', 'Load Power'),
    'pv_voltage': Gauge('solarmon_solar_volts', 'Solar Voltage'),
    'pv_current': Gauge('solarmon_solar_amperes', 'Solar Current'),
    'pv_power': Gauge('solarmon_solar_watts', 'Solar Power'),
    'max_charging_power_today': Gauge('solarmon_max_charging_power_today', 'Max Charging Power Today'),
    'max_discharging_power_today': Gauge('solarmon_max_discharging_power_today', 'Max Discharging Power Today'),
    'charging_amp_hours_today': Gauge('solarmon_charging_amp_hours_today', 'Charging Amp Hours Today'),
    'discharging_amp_hours_today': Gauge('solarmon_discharging_amp_hours_today', 'Discharging Amp Hours Today'),
    'power_generation_today': Gauge('solarmon_power_generation_today', 'Power Generation Today'),
    'power_consumption_today': Gauge('solarmon_power_consumption_today', 'Power Consumption Today'),
    'power_generation_total': Gauge('solarmon_power_generation_total', 'Power Generation Total'),
    'charging_status': Gauge('solarmon_controller_charging_state', 'Charging Status'),
    'pi_temp': Gauge('pi_temperature_celcius', 'Pi Temperature'),
    'pi_cpu': Gauge('pi_cpu_usage', 'Pi CPU Usage'),
    'pi_ram': Gauge('pi_ram_usage', 'Pi RAM Usage'),
    'pi_storage': Gauge('pi_storage_usage', 'Pi Storage Capacity'),
}

class prometheus_logger:
    def __init__(self):
        logging.info("Starting Prometheus Server")
        start_http_server(5000)

    def data_received_callback(self, data):
        for key in data:
            value = data[key]
            logging.info("{}: {}".format(key, value))
            gauge = prometheus_map[key]
            gauge.set(value)

        # Append Pi stats
        gauge = prometheus_map['pi_temp']
        gauge.set(CPUTemperature().temperature)

        gauge = prometheus_map['pi_cpu']
        gauge.set(psutil.cpu_percent())

        gauge = prometheus_map['pi_ram']
        gauge.set(psutil.virtual_memory().percent)

        gauge = prometheus_map['pi_storage']
        gauge.set(psutil.disk_usage('/').percent)
