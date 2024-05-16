"""Module for parsing of message data types."""

import re

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Callable, Tuple, Generic, TypeVar

from loguru import logger
from result import Ok, Err, Result

from .data_types import (
    AuvMessageHeader,
    ImageCaptureDataV1,
    ImageCaptureDataV2,
    TeledyneDVLData,
    LQModemData,
    EvologicsModemData,
    BatteryData,
    ThrusterData,
)


THRUSTER_TOPIC_TO_NAME: Dict[str, str] = {
    "THR_PORT": "thruster_portside",
    "THR_STBD": "thruster_starboard",
    "THR_VERT": "thruster_vertical",
}

BATTERY_TOPIC_TO_NAME: Dict[str, str] = {
    "BATT": "battery",
    "BATT0": "battery_00",
    "BATT1": "battery_01",
    "BATT2": "battery_02",
}


"""
Image message parsers:
- parse_image_message_v1
- parse_image_message_v2
"""


type ParseResult = Result[Any, str]


def parse_image_message_v1(header: AuvMessageHeader, line: str) -> ParseResult:
    """Parses a message line as an image message.

    VIS: 1244853280.578  [1244853280.348234] PR_20090613_003440_348_LC16.pgm
    """

    pattern = re.compile(
        r"""
        \s*\[(?P<trigger_time>\d+.\d+)\]    # whitespaces, left bracket, trigger time, right bracket
        \s*(?P<label>[\w]+)                 # whitespaces, label (filename stem)
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse body: {line}")

    body = ImageCaptureDataV1(
        trigger_time=float(match["trigger_time"]), label=str(match["label"])
    )

    return Ok(body)


def parse_image_message_v2(header: AuvMessageHeader, line: str) -> ParseResult:
    """Parses a message line as an image message.

    VIS: 1370910671.991  [1370910671.168201] PR_20130611_003111_168_LC16.tif exp: 1592
    """

    pattern = re.compile(
        r"""
        \s*\[(?P<trigger_time>\d+.\d+)\]    # whitespace, trigger time
        \s*(?P<label>[\w]+)\.[\w]+          # whitespace, label, extension
        \s*exp:\s*(?P<exposure>[\d]+)       # whitespace, key, exposure
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    body = ImageCaptureDataV2(
        trigger_time=float(match["trigger_time"]),
        label=str(match["label"]),
        exposure=int(match["exposure"]),
    )

    return Ok(body)


"""
Navigation data parsers:
- parse_teledyne_dvl_message
- parse_lq_modem_message
- parse_evologics_modem_message
"""


def parse_teledyne_dvl_message(header: AuvMessageHeader, line: str) -> TeledyneDVLData:
    """Parses a message line as a TeledyneDVLData dataclass."""

    pattern = re.compile(
        r"""
        \s*alt:\s*(?P<altitude>[-+]?\d*[.]\d*)
        \s*r1:\s*(?P<range_01>[-+]?\d*[.]\d*)
        \s*r2:\s*(?P<range_02>[-+]?\d*[.]\d*)
        \s*r3:\s*(?P<range_03>[-+]?\d*[.]\d*)
        \s*r4:\s*(?P<range_04>[-+]?\d*[.]\d*)
        \s*h:\s*(?P<heading>[-+]?\d*[.]\d*)
        \s*p:\s*(?P<pitch>[-+]?\d*[.]\d*)
        \s*r:\s*(?P<roll>[-+]?\d*[.]\d*)
        \s*vx:\s*(?P<velocity_x>[-+]?\d*[.]\d*)
        \s*vy:\s*(?P<velocity_y>[-+]?\d*[.]\d*)
        \s*vz:\s*(?P<velocity_z>[-+]?\d*[.]\d*)
        \s*nx:\s*(?P<position_x>[-+]?\d*[.]\d*)
        \s*ny:\s*(?P<position_y>[-+]?\d*[.]\d*)
        \s*nz:\s*(?P<position_z>[-+]?\d*[.]\d*)
        \s*COG:\s*(?P<course_over_ground>[-+]?\d*[.]\d*)
        \s*SOG:\s*(?P<speed_over_ground>[-+]?\d*[.]\d*)
        \s*bt_status:\s*(?P<bottom_track_status>\d*)
        \s*h_true:\s*(?P<true_heading>[-+]?\d*[.]\d*)
        \s*p_gimbal:\s*(?P<gimbal_pitch>[-+]?\d*[.]\d*)
        \s*sv:\s*(?P<sound_velocity>[-+]?\d*[.]\d*)
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse line: {line}")

    data = TeledyneDVLData(
        altitude=float(match["altitude"]),
        range_01=float(match["range_01"]),
        range_02=float(match["range_02"]),
        range_03=float(match["range_03"]),
        range_04=float(match["range_04"]),
        heading=float(match["heading"]),
        pitch=float(match["pitch"]),
        roll=float(match["roll"]),
        velocity_x=float(match["velocity_x"]),
        velocity_y=float(match["velocity_y"]),
        velocity_z=float(match["velocity_z"]),
        position_x=float(match["position_x"]),
        position_y=float(match["position_y"]),
        position_z=float(match["position_z"]),
        course_over_ground=float(match["course_over_ground"]),
        speed_over_ground=float(match["speed_over_ground"]),
        true_heading=float(match["true_heading"]),
        gimbal_pitch=float(match["gimbal_pitch"]),
        sound_velocity=float(match["sound_velocity"]),
        bottom_track_status=int(match["bottom_track_status"]),
    )

    logger.info(data)

    return Ok(data)


def parse_paroscientific_message(header: AuvMessageHeader, line: str) -> object:
    """Parses a message line as a Paroscientific dataclass."""
    raise NotImplementedError("parse_paroscientific_message is not implemented.")


def parse_lq_modem_message(header: AuvMessageHeader, line: str) -> LQModemData:
    """Parses a message line as a LQModemData dataclass."""

    pattern = re.compile(
        r"""
        \s*time:\s*(?P<time>\d*[.]\d*)
        \s*Lat:\s*(?P<latitude>[-+]?\d*[.]\d*)
        \s*Lon:\s*(?P<longitude>[-+]?\d*[.]\d*)
        \s*hdg:\s*(?P<heading>[-+]?\d*[.]\d*)
        \s*roll:\s*(?P<roll>[-+]?\d*[.]\d*)
        \s*pitch:\s*(?P<pitch>[-+]?\d*[.]\d*)
        \s*bear:\s*(?P<bearing>[-+]?\d*[.]\d*)
        \s*rng:\s*(?P<range>[-+]?\d*[.]\d*)
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse line: {line}")

    data = LQModemData(
        latitude=float(match["latitude"]),
        longitude=float(match["longitude"]),
        roll=float(match["roll"]),
        pitch=float(match["pitch"]),
        heading=float(match["heading"]),
        bearing=float(match["bearing"]),
        range=float(match["range"]),
    )

    return Ok(data)


def parse_evologics_modem_message(
    header: AuvMessageHeader, line: str
) -> EvologicsModemData:
    """Parses a message line as an Evologics USBL message.

    EVOLOGICS_FIX: 1495772673.026 target_lat:-28.813446502 target_lon:113.947151550
    target_depth:12.357 accuracy:3.537 ship_lat:-28.812462645 ship_lon:113.946070301
    ship_roll: -1.61 ship_pitch: -0.01 ship_heading:270.35 target_x:-54.63 target_y:-141.69
    target_z: -4.48
    """

    pattern = re.compile(
        r"""
        \s*target_lat:\s*(?P<target_latitude>[-+]?\d*[.]\d*)
        \s*target_lon:\s*(?P<target_longitude>[-+]?\d*[.]\d*)
        \s*target_depth:\s*(?P<target_depth>[-+]?\d*[.]\d*)
        \s*accuracy:\s*(?P<accuracy>[-+]?\d*[.]\d*)
        \s*ship_lat:(?P<ship_latitude>[-+]?\d*[.]\d*)
        \s*ship_lon:\s*(?P<ship_longitude>\d*[.]\d*)
        \s*ship_roll:\s*(?P<ship_roll>[-+]?\d*[.]\d*)
        \s*ship_pitch:\s*(?P<ship_pitch>[-+]?\d*[.]\d*)
        \s*ship_heading:\s*(?P<ship_heading>\d*[.]\d*)
        \s*target_x:\s*(?P<target_x>[-+]?\d*[.]\d*)
        \s*target_y:\s*(?P<target_y>[-+]?\d*[.]\d*)
        \s*target_z:\s*(?P<target_z>[-+]?\d*[.]\d*)
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse line: {line}")

    data = EvologicsModemData(
        target_latitude=float(match["target_latitude"]),
        target_longitude=float(match["target_longitude"]),
        target_depth=float(match["target_depth"]),
        target_x=float(match["target_x"]),
        target_y=float(match["target_y"]),
        target_z=float(match["target_z"]),
        accuracy=float(match["accuracy"]),
        ship_latitude=float(match["ship_latitude"]),
        ship_longitude=float(match["ship_longitude"]),
        ship_roll=float(match["ship_roll"]),
        ship_pitch=float(match["ship_pitch"]),
        ship_heading=float(match["ship_heading"]),
    )

    return Ok(data)


def parse_thruster_message(header: AuvMessageHeader, line: str) -> ThrusterData:
    """Parser function for thruster messages.

    THR_PORT:  1244855390.607        RPM:0.00 A:0.0400 V:46.80 T:29.00
    """
    pattern = re.compile(
        r"""
        \s*RPM:\s*(?P<rpm>[-+]?\d*[.]\d*)                  # rpm
        \s*A:\s*(?P<current>[-+]?\d*[.]\d*)                # current
        \s*V:\s*(?P<voltage>[-+]?\d*[.]\d*)                # voltage
        \s*T:\s*(?P<temperature>[-+]?\d*[.]\d*)            # temperature
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse line: {line}")

    if not header.topic in THRUSTER_TOPIC_TO_NAME:
        return Err(f"unknown thruster name for topic: {header.topic}")

    body = ThrusterData(
        name=THRUSTER_TOPIC_TO_NAME[header.topic],
        rpm=float(match["rpm"]),
        current=float(match["current"]),
        voltage=float(match["voltage"]),
        temperature=float(match["temperature"]),
    )

    return Ok(body)


"""
Power system data parsers:
- parse_battery_message
- parse_thruster_message
"""


def parse_battery_message(header: AuvMessageHeader, line: str) -> ParseResult:
    """Parses a message line as a BatteryMessage object."""

    pattern = re.compile(
        r"""
        \s*TimeLeft:\s*(?P<time_left>\d+)
        \s*PercentCharge:\s*(?P<charge_percent>\d+)
        \s*Current:\s*(?P<current>[-+]?\d+[.]\d+)
        \s*Voltage:\s*(?P<voltage>\d+[.]\d+)
        \s*Power:\s*(?P<power>\d+[.]\d+)
        \s*Charging:\s*(?P<charging>\d)
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse line: {line}")

    if not header.topic in BATTERY_TOPIC_TO_NAME:
        return Err(f"unknown battery name for topic: {header.topic}")

    body = BatteryData(
        name=BATTERY_TOPIC_TO_NAME[header.topic],
        time_left=int(match["time_left"]),
        current=float(match["current"]),
        voltage=float(match["voltage"]),
        power=float(match["power"]),
        charge_percent=int(match["charge_percent"]),
        charging=bool(int(match["charging"])),
    )

    return Ok(body)


ParseFun = Callable[[str], Any]


# Temporary: Remove after development is done
PROTOCOL_DEV: Dict[str, ParseFun] = {
    "VIS": parse_image_message_v1,
    "RDI": parse_teledyne_dvl_message,
    "LQMODEM": parse_lq_modem_message,
    "EVOLOGICS_FIX": parse_evologics_modem_message,
    "THR_PORT": parse_thruster_message,
    "THR_STBD": parse_thruster_message,
    "THR_VERT": parse_thruster_message,
    "BATT": parse_battery_message,
    "BATT0": parse_battery_message,
    "BATT1": parse_battery_message,
    "BATT2": parse_battery_message,
}

PROTOCOL_V1: Dict[str, ParseFun] = {
    "VIS": parse_image_message_v1,
    "RDI": parse_teledyne_dvl_message,
    "LQMODEM": parse_lq_modem_message,
    "THR_PORT": parse_thruster_message,
    "THR_STBD": parse_thruster_message,
    "THR_VERT": parse_thruster_message,
    "BATT": parse_battery_message,
    "BATT0": parse_battery_message,
    "BATT1": parse_battery_message,
    "BATT2": parse_battery_message,
}

PROTOCOL_V2: Dict[str, ParseFun] = {
    "VIS": parse_image_message_v2,
    "RDI": parse_teledyne_dvl_message,
    "LQMODEM": parse_lq_modem_message,
    "THR_PORT": parse_thruster_message,
    "THR_STBD": parse_thruster_message,
    "THR_VERT": parse_thruster_message,
    "BATT": parse_battery_message,
    "BATT0": parse_battery_message,
    "BATT1": parse_battery_message,
    "BATT2": parse_battery_message,
}
