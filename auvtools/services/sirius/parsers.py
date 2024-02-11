""" """

import re

from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from loguru import logger
from result import Ok, Err, Result

from .messages import MessageIDs, MessageNames, MessageHeader, MessageData

MessageParseFunc = Callable[str, MessageData]

UNKNOWN_EXPOSURE = 2500

# TODO: Add message field description - ability to specifiy key and value type. 
# Set up maps from original field name to field description.

CTD_FIELD_MAP = {
    "cond" : "conductivity",
    "temp" : "temperature",
    "sal" : "salinity",
    "pres" : "pressure",
    "sos" : "sound_velocity",
}

DOPPLER_FIELD_MAP = {
    "alt" : "altitude",
    "r1" : "range_1",
    "r2" : "range_2",
    "r3" : "range_3",
    "r4" : "range_4",
    "h" : "heading",
    "p" : "pitch",
    "r" : "roll",
    "vx" : "velocity_x",
    "vy" : "velocity_y",
    "vz" : "velocity_z",
    "nx" : "relative_position_x", # TODO: Verify - order of mag. seems reasonable
    "ny" : "relative_position_y", # TODO: Verify - order of mag. seems reasonable
    "nz" : "relative_position_z", # TODO: Verify - correlates with pressure sensor
    "COG" : "cog",
    "SOG" : "sog",
    "bt_status" : "bt_status",
    "h_true" : "heading_true",
    "p_gimbal" : "pitch_gimbal",
    "sv" : "sound_velocity",
}

ECHOSOUNDER_FIELD_MAP = {
    "ProfRng" : "profile_range",
    "PseudoAlt" : "pseudo_altitude",
    "PseudoFwdDistance" : "pseudo_forward_distance",
    "Angle" : "angle",
}

ECOPUCK_FIELD_MAP = {
    "chlor"  : "chlorophyll",
    "bcksct" : "backscatter",
    "cdom"   : "cdom",
    "temp"   : "temperature",
}

THRUSTER_FIELD_MAP = {
    "RPM" : "rpm",
    "A" : "current",
    "V" : "voltage",
    "T" : "temperature",
}

LQMODEM_FIELD_MAP = {
    "time"    : "timestamp",
    "Lat"     : "latitude",
    "Lon"     : "longitude",
    "hdg"     : "heading",
    "roll"    : "roll",
    "pitch"   : "pitch",
    "bear"    : "bearing",
    "rng"     : "range",
}

GPS_FIELD_MAP = {
    "Lat" : "latitude",
    "Lon" : "longitude",
    "Bad" : "bad",
    "Spd" : "speed",
    "Crs" : "crs",
    "Mg"  : "magnetic",
}

BATTERY_FIELD_MAP = {
    "TimeLeft"      : "time_left",
    "PercentCharge" : "percent_charge",
    "Current"       : "current",
    "Voltage"       : "voltage",
    "Power"         : "power",
    "Charging"      : "charging",
}

# -----------------------------------------------------------------------------
# ---- Message utility functions ----------------------------------------------
# -----------------------------------------------------------------------------

def is_float_castable(string: str) -> bool:
    """ Returns true if the string can be interpreted as a float. """
    try:
        float(string)
        return True
    except ValueError:
        return False

def remap_dictionary_keys(data: Dict, key_map: Dict) -> Dict:
    """ Changes the key in data that have a mapping in the key map. """
    # Update keymap with unmapped keys from data
    key_map.update( { key : key for key in data if key not in key_map } )
    return { key_map[key]: value for key, value in data.items() }

def get_message_identifier(message: str) -> Result[str, str]:
    """ Extracts the identifier from a message string."""
    splits = message.split(":")
    if len(splits) == 0:
        return Err(f"unable to parse identifier for message: {0}")
    return Ok(splits[0])

def read_message_header(message: str) -> MessageHeader:
    """ Parse the header from a message string. """
    entries = [ entry for entry in message.split(" ") if entry ]
    identifier, timestamp = entries[0].split(":")
    return MessageHeader(
        identifier = identifier,
        timestamp = float(timestamp),
    )

def read_message_payload(message: str) -> str:
    """ Parse the header from a message string. """
    entries = [ entry for entry in message.split(" ") if entry ]
    return " ".join(entries[1:])

def cast_dictionary_values_to_float(data: Dict) -> Dict:
    """ Casts dictionary values to float if the conversion is valid. """
    for key, value in data.items():
        data[key] = float(value) if is_float_castable(value) else value
    return data

# -----------------------------------------------------------------------------
# ---- Message parsers --------------------------------------------------------
# -----------------------------------------------------------------------------

def parse_fielded_message(
    message: str, 
    remapped_keys: Dict[str, str],
) -> MessageData:
    """ 
    Parse a fielded message, i.e. a message where the payload consists of pairs 
    of keys and values. 
    """
    header = read_message_header(message)
    payload_string = read_message_payload(message)
    
    # Format payload string
    payload_string = payload_string.strip()
    
    # Cast numerical strings to float
    fields = dict(item.split(":") for item in payload_string.split(" "))
    fields = cast_dictionary_values_to_float(fields)

    # Remap dictionary keys
    payload = remap_dictionary_keys(fields, remapped_keys)
    return MessageData(header, payload)

def parse_ctd_message(message: str) -> MessageData:
    """ Parser function for CTD messages. """
    return parse_fielded_message(message, CTD_FIELD_MAP)

def parse_doppler_log_message(message: str) -> MessageData:
    """ Parser function for Doppler log messages. """
    return parse_fielded_message(message, DOPPLER_FIELD_MAP)

def parse_echosounder_message(message: str) -> MessageData:
    """ Parser function for echosounder messages. """
    return parse_fielded_message(message, ECHOSOUNDER_FIELD_MAP)

def parse_ecopuck_message(message: str) -> MessageData:
    """ Parser function for Ecopuck messages. """
    return parse_fielded_message(message, ECOPUCK_FIELD_MAP)

def parse_thruster_message(message: str) -> MessageData:
    """ Parser function for thruster messages. """
    return parse_fielded_message(message, THRUSTER_FIELD_MAP)

def parse_lqmodem_message(message: str) -> MessageData:
    """ Parser function for LQ modem messages. """
    return parse_fielded_message(message, LQMODEM_FIELD_MAP)

def parse_battery_message(message: str) -> MessageData:
    """ Parser function for battery messages. """
    return parse_fielded_message(message, BATTERY_FIELD_MAP)

# -----------------------------------------------------------------------------
# ---- Special message parsers ------------------------------------------------
# -----------------------------------------------------------------------------

def parse_image_message(message: str) -> MessageData:
    """ 
    Parser function for visual sensor messages. 

    Example messages:
    VIS: 1244853280.578  [1244853280.348234] PR_20090613_003440_348_LC16.pgm
    VIS: 1370910671.991  [1370910671.168201] PR_20130611_003111_168_LC16.tif exp: 1592
    """
    header = read_message_header(message)
    payload_string = read_message_payload(message)

    entries = payload_string.split(" ")

    time = float(entries[0])
    label = str(Path(entries[1]).stem)

    if label.endswith("_LM16") or label.endswith("_LC16"):
        source = "left"
    elif label.endswith("_RM16") or label.endswith("_RC16"):
        source = "right"
    else:
        source = "unknown"

    if len(entries) > 2:
        _, exposure = entries[2].split(":")
        exposure_mode = "adaptive"
        exposure_value = int(exposure)
    else:
        exposure_mode = "unknown"
        exposure_value = UNKNOWN_EXPOSURE

    payload = {
        "time" : time,
        "label" : label,
        "source" : source,
        "exposure_mode" : exposure_mode,
        "exposure_value" : exposure_value,
    }

    return MessageData(header, payload)

def parse_pressure_message(message: str) -> MessageData:
    """ 
    Parser function for pressure sensor messages. 

    Example message:
    PAROSCI:  1244853355.812	28.5529
    """
    header = read_message_header(message)
    payload_string = read_message_payload(message)
    
    payload = { "depth" : float(payload_string) }
    return MessageData(header, payload)

def parse_gps_message(message: str) -> MessageData:
    """ 
    GPS_RMC:  1370910445.897 Lat:-41.253271667 S Lon:148.342691667 E  Bad:   0 A Spd:0.400 Crs:0.000 Mg:-1.000
    """
    header = read_message_header(message)
    payload_string = read_message_payload(message)

    entries = payload_string.split(" ")
    entries = [ entry for entry in entries if ":" in entry ]

    fields = dict(item.split(":") for item in entries)
    fields = cast_dictionary_values_to_float(fields)

    remapped_keys = {
        "Lat" : "latitude",
        "Lon" : "longitude",
        "Bad" : "bad",
        "Spd" : "speed",
        "Crs" : "crs",
        "Mg"  : "magnetic",
    }

    payload = remap_dictionary_keys(fields, remapped_keys)
    return MessageData(header, payload)

# -----------------------------------------------------------------------------
# ---- Default message parsers ------------------------------------------------
# -----------------------------------------------------------------------------

DEFAULT_MESSAGE_PARSERS = {
    "THR_PORT" : parse_thruster_message,
    "THR_STBD" : parse_thruster_message,
    "THR_VERT" : parse_thruster_message,
    "LQMODEM"  : parse_lqmodem_message,

    "GPS_RMC"  : parse_gps_message,
    "MICRON" : parse_echosounder_message,
    "MICRON_RETURNS" : parse_echosounder_message,

    "BATT0" : parse_battery_message,
    "BATT1" : parse_battery_message,
    "BATT2" : parse_battery_message,

    "RDI"      : parse_doppler_log_message,
    "OAS"      : parse_echosounder_message,
    "PAROSCI"  : parse_pressure_message,
    "SEABIRD"  : parse_ctd_message,
    "VIS"      : parse_image_message,
    "ECOPUCK"  : parse_ecopuck_message,
}

# Validate message parsers
for identifier in MessageIDs:
    assert identifier in DEFAULT_MESSAGE_PARSERS, \
        f"found no parser for message identifier {identifier}"

# -----------------------------------------------------------------------------
# ---- String processors ------------------------------------------------------
# -----------------------------------------------------------------------------

def remove_subsequent_whitespaces(string: str) -> str:
    """ Removes subsequent whitespaces from a string. """
    return re.sub(" +", " ", string)

def remove_ending_whitespaces(string: str) -> str:
    """ Removes leading and trailing whitespaces from a string. """
    return string.strip()

def remove_brackets(string: str) -> str:
    """ Removes square bracket characters from a string."""
    return string.replace("[", "").replace("]", "")

def replace_characters(string: str, target: str, replacement: str) -> str:
    """ Replaces tab characters from a string."""
    return string.replace(target, replacement)

def condense_key_value_pairs(string: str) -> str:
    """ Removes whitespace after semicolons to condense key-value pairs. """
    return string.replace(": ", ":")

# -----------------------------------------------------------------------------
# ---- Parse tasks ------------------------------------------------------------
# -----------------------------------------------------------------------------

def parse_messages(
    lines: List[str],
    parsers: Dict[str, MessageParseFunc] = DEFAULT_MESSAGE_PARSERS
):
    """ 
    Parse a collection of messages and return the parsed message data. The
    parser for each message type is based on the identifier of the message.
    """
    unparsed_identifiers = set()
    messages = list()
    for line in lines:
        # TODO: Inject message identifier
        result : Result[str, str] = get_message_identifier(line)

        if result.is_err():
            logger.error(f"invalid message identifier")
                
        identifier = result.unwrap()

        if not identifier in parsers:
            unparsed_identifiers.add(identifier)
            continue

        processors = [
            remove_subsequent_whitespaces,
            remove_ending_whitespaces,
            partial(replace_characters, target="[", replacement=""),
            partial(replace_characters, target="]", replacement=""),
            partial(replace_characters, target="\t", replacement=" "),
            partial(replace_characters, target=": ", replacement=":"),
        ]
        
        # Process message string
        for processor in processors:
            line = processor(line)
       
        message = parsers[identifier](line)
        messages.append(message)
    
    for identifier in unparsed_identifiers:
        logger.warning(f"no parser for message identifier: {identifier}")
    
    return messages
