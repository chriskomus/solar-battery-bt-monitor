# ------------------------------------------------------
# junctek_app.py
# Author: Chris Komus
# https://github.com/chriskomus/solar-battery-bt-monitor
#
# Feel free to reuse this code for any purpose
# ------------------------------------------------------
import logging

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

# def sssss(data, battery_capacity_ah, start_script_as_charging):
#     """
#     Gets the binary data from the BLE-device and converts it to a byte stream
#     """
#     bs = str(data.hex()).upper()

#     if not validate(bs):
#         return False

#     values = parse_incoming_bytestream(bs)
#     formatted_values = format_values(values)
#     # logging.debug(formatted_values)
#     return handleMessage(formatted_values)


def validate(bs):
    """
    Validate that the data has a valid start of stream and end of stream,
    and contains at least one known parameter.
    """
    if bs == None:
        logging.warning("Empty BS {}".format(bs))
        return False

    if not bs.startswith(BEGINNING_OF_STREAM):
        logging.warning("Incorrect beginning of stream: {}".format(bs))
        return False

    if not bs.endswith(END_OF_STREAM):
        logging.warning("Incorrect end of stream: {}".format(bs))
        return False

    if not [v for v in PARAM_KEYS.values() if v in bs]:
        # logging.debug("No parameters found in stream: {}".format(bs))
        return False

    return True


def parse_incoming_bytestream(bs, battery_capacity_ah, charging):
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
    params_keys = list(PARAM_KEYS.keys())
    params_values = list(PARAM_KEYS.values())

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


# def charging_state(self, values):
#     """
#     Determine charging state and return True if charging
#     """
#     if values["dir_of_current"] == "01"


# def handleMessage(self, values):
#     if not values:
#         return False

#     if "voltage" in values:
#         self.PowerDevice.entities.voltage = values["voltage"]
#     if "current" in values:
#         self.PowerDevice.entities.current = values["current"]
#     if "power" in values:
#         self.PowerDevice.entities.power = values["power"]
#     if "max_capacity" in values:
#         self.PowerDevice.entities.max_capacity = values["max_capacity"]
#     if "ah_remaining" in values:
#         self.PowerDevice.entities.exp_capacity = values["ah_remaining"]
#     if "mins_remaining" in values:
#         self.PowerDevice.entities.mins_remaining = values["mins_remaining"]
#     if "soc" in values:
#         self.PowerDevice.entities.soc = values["soc"]
#     if "temp" in values:
#         self.PowerDevice.entities.temperature_celsius = values["temp"]

#     return True
