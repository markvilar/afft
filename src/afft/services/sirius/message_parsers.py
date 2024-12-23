"""Module for parsing of message data types."""

import re

from pathlib import Path
from typing import Optional

from ...utils.result import Ok, Err, Result

from .message_interfaces import MessageParser
from .concrete_messages import (
    MessageHeader,
    ImageCaptureMessage,
    SeabirdCTDMessage,
    AanderaaCTDMessage,
    EcopuckMessage,
    ParosciPressureMessage,
    TeledyneDVLMessage,
    TrackLinkModemMessage,
    EvologicsModemMessage,
    MicronSonarMessage,
    OASonarMessage,
    BatteryMessage,
    ThrusterMessage,
)


MESSAGE_HEADER_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+).*   # unlimited of any character after timestamp
    $
    """

IMAGE_CAPTURE_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    (\[(?P<trigger_time>\d+.\d+)\])\s+
    (?P<filename>[\w]+\.[\w]+)\s*       # Zero or unlimited since next group is optional
    (exp:\s+(?P<exposure>\d+))?\s*      # Optional exposure group
    $
    """

SEABIRD_CTD_REGEX = r"""
    ^
    (?P<topic>\w+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    cond:(?P<conductivity>[-+]?\d+\.\d+)\s+
    temp:(?P<temperature>[-+]?\d+\.\d+)\s+
    sal:(?P<salinity>[-+]?\d+\.\d+)\s+
    pres:(?P<pressure>[-+]?\d+\.\d+)\s+
    sos:(?P<sound_velocity>[-+]?\d+\.\d+)\s*
    $
    """

AANDERAA_CTD_REGEX = r"""
    ^
    (?P<topic>\w+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    cond:(?P<conductivity>[-+]?\d+\.\d+)\s+
    temp:(?P<temperature>[-+]?\d+\.\d+)\s+
    sal:(?P<salinity>[-+]?\d+\.\d+)\s+
    pres:(?P<pressure>[-+]?\d+\.\d+)\s+
    sos:(?P<sound_velocity>[-+]?\d+\.\d+)\s*
    $
    """

ECOPUCK_REGEX = r"""
    ^
    (?P<topic>\w+):\s+
    (?P<timestamp>[-+]?\d+\.\d+)\s+
    chlor:(?P<chlorophyll>[-+]?\d+\.\d+)\s+
    bcksct:(?P<backscatter>[-+]?\d+\.\d+)\s+
    cdom:(?P<cdom>[-+]?\d+\.\d+)\s+
    temp:(?P<temperature>[-+]?\d+\.\d+)\s*
    $
    """

PAROSCI_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    (?P<depth>[-+]?\d+\.\d+)\s*
    $
    """

TELEDYNE_DVL_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    alt:\s*(?P<altitude>[-+]?\d*[.]\d*)\s+
    r1:\s*(?P<range_01>[-+]?\d*[.]\d*)\s+
    r2:\s*(?P<range_02>[-+]?\d*[.]\d*)\s+
    r3:\s*(?P<range_03>[-+]?\d*[.]\d*)\s+
    r4:\s*(?P<range_04>[-+]?\d*[.]\d*)\s+
    h:\s*(?P<heading>[-+]?\d*[.]\d*)\s+
    p:\s*(?P<pitch>[-+]?\d*[.]\d*)\s+
    r:\s*(?P<roll>[-+]?\d*[.]\d*)\s+
    vx:\s*(?P<velocity_x>[-+]?\d*[.]\d*)\s+
    vy:\s*(?P<velocity_y>[-+]?\d*[.]\d*)\s+
    vz:\s*(?P<velocity_z>[-+]?\d*[.]\d*)\s+
    nx:\s*(?P<dmg_x>[-+]?\d*[.]\d*)\s+
    ny:\s*(?P<dmg_y>[-+]?\d*[.]\d*)\s+
    nz:\s*(?P<dmg_z>[-+]?\d*[.]\d*)\s+
    COG:\s*(?P<course_over_ground>[-+]?\d*[.]\d*)\s+
    SOG:\s*(?P<speed_over_ground>[-+]?\d*[.]\d*)\s+
    bt_status:\s*(?P<bottom_track_status>\d*)\s+
    h_true:\s*(?P<true_heading>[-+]?\d*[.]\d*)\s+
    p_gimbal:\s*(?P<gimbal_pitch>[-+]?\d*[.]\d*)\s+
    sv:\s*(?P<sound_velocity>[-+]?\d*[.]\d*)\s*
    $
    """

LQ_MODEM_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    time:\s*(?P<time>[-+]?\d*[.]\d*)\s+
    Lat:\s*(?P<latitude>[-+]?\d*[.]\d*)\s+
    Lon:\s*(?P<longitude>[-+]?\d*[.]\d*)\s+
    hdg:\s*(?P<heading>[-+]?\d*[.]\d*)\s+
    roll:\s*(?P<roll>[-+]?\d*[.]\d*)\s+
    pitch:\s*(?P<pitch>[-+]?\d*[.]\d*)\s+
    bear:\s*(?P<bearing>[-+]?\d*[.]\d*)\s+
    rng:\s*(?P<range>[-+]?\d*[.]\d*)\s*
    $
    """

EVOLOGICS_MODEM_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    target_lat:\s*(?P<target_latitude>[-+]?\d*[.]\d*)\s+
    target_lon:\s*(?P<target_longitude>[-+]?\d*[.]\d*)\s+
    target_depth:\s*(?P<target_depth>[-+]?\d*[.]\d*)\s+
    accuracy:\s*(?P<accuracy>[-+]?\d*[.]\d*)\s+
    ship_lat:(?P<ship_latitude>[-+]?\d*[.]\d*)\s+
    ship_lon:\s*(?P<ship_longitude>\d*[.]\d*)\s+
    ship_roll:\s*(?P<ship_roll>[-+]?\d*[.]\d*)\s+
    ship_pitch:\s*(?P<ship_pitch>[-+]?\d*[.]\d*)\s+
    ship_heading:\s*(?P<ship_heading>\d*[.]\d*)\s+
    target_x:\s*(?P<target_x>[-+]?\d*[.]\d*)\s+
    target_y:\s*(?P<target_y>[-+]?\d*[.]\d*)\s+
    target_z:\s*(?P<target_z>[-+]?\d*[.]\d*)\s*
    $
    """

MICRON_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    ProfRng:\s*(?P<profile_range>[-+]?\d+\.\d+)\s+
    PseudoAlt:\s*(?P<profile_altitude>[-+]?\d+\.\d+)\s+
    PseudoFwdDistance:\s*(?P<pseudo_forward_distance>[-+]?\d+\.\d+)\s+
    Angle:\s*(?P<angle>[-+]?\d+\.\d+).*
    $
    """

OAS_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    ProfRng:\s*(?P<profile_range>[-+]?\d+\.\d+)\s+
    PseudoAlt:\s*(?P<profile_altitude>[-+]?\d+\.\d+)\s+
    PseudoFwdDistance:\s*(?P<pseudo_forward_distance>[-+]?\d+\.\d+).*
    $
    """

THRUSTER_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    RPM:\s*(?P<rpm>[-+]?\d*[.]\d*)\s+
    A:\s*(?P<current>[-+]?\d*[.]\d*)\s+
    V:\s*(?P<voltage>[-+]?\d*[.]\d*)\s+
    T:\s*(?P<temperature>[-+]?\d*[.]\d*)\s*
    $
    """

BATTERY_REGEX = r"""
    ^
    (?P<topic>\w+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    TimeLeft:\s*(?P<time_left>[-+]?\d+)\s+
    PercentCharge:\s*(?P<charge_percent>\d+)\s+
    Current:\s*(?P<current>[-+]?\d+[.]\d+)\s+
    Voltage:\s*(?P<voltage>[-+]?\d+[.]\d+)\s+
    Power:\s*(?P<power>[-+]?\d+[.]\d+)\s+
    Charging:\s*(?P<charging>\d)\s*
    $
    """


def parse_message_header(line: str) -> Result[MessageHeader, str]:
    """Parses the header from a message line."""

    pattern = re.compile(MESSAGE_HEADER_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse header: {line}")

    header = MessageHeader(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    return Ok(header)


def parse_image_message(line: str) -> Result[ImageCaptureMessage, str]:
    """Parses a message line as an image capture message."""

    pattern = re.compile(IMAGE_CAPTURE_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse image message: {line}")

    header = ImageCaptureMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    filename: str = str(match["filename"])
    label: str = Path(match["filename"]).stem
    trigger_time: float = float(match["trigger_time"])
    exposure_logged: bool = match["exposure"] is not None

    exposure: int = int(match["exposure"]) if exposure_logged else 0

    body = ImageCaptureMessage.body_type(
        label=label,
        filename=filename,
        trigger_time=trigger_time,
        exposure_logged=exposure_logged,
        exposure=exposure,
    )

    return Ok(ImageCaptureMessage(header, body))


def parse_seabird_ctd_message(line: str) -> Result[SeabirdCTDMessage, str]:
    """Parses a message line as a Seabird CTD message."""

    pattern = re.compile(SEABIRD_CTD_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse Seabird CTD message: {line}")

    header = SeabirdCTDMessage.header_type(
        topic=str(match["topic"]), timestamp=float(match["timestamp"])
    )

    body = SeabirdCTDMessage.body_type(
        conductivity=float(match["conductivity"]),
        temperature=float(match["temperature"]),
        salinity=float(match["salinity"]),
        pressure=float(match["pressure"]),
        sound_velocity=float(match["sound_velocity"]),
    )

    return Ok(SeabirdCTDMessage(header, body))


def parse_aanderaa_ctd_message(line: str) -> Result[AanderaaCTDMessage, str]:
    """Parses a message line as an Aanderaa CTD message."""

    pattern = re.compile(AANDERAA_CTD_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse Aanderaa CTD message: {line}")

    header = AanderaaCTDMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = AanderaaCTDMessage.body_type(
        conductivity=float(match["conductivity"]),
        temperature=float(match["temperature"]),
        salinity=float(match["salinity"]),
        pressure=float(match["pressure"]),
        sound_velocity=float(match["sound_velocity"]),
    )

    return Ok(AanderaaCTDMessage(header, body))


def parse_ecopuck_message(line: str) -> Result[EcopuckMessage, str]:
    """Parses a message line as an Ecopuck water quality message."""

    pattern = re.compile(ECOPUCK_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse Ecopuck message: {line}")

    header = EcopuckMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = EcopuckMessage.body_type(
        chlorophyll=float(match["chlorophyll"]),
        backscatter=float(match["backscatter"]),
        cdom=float(match["cdom"]),
        temperature=float(match["temperature"]),
    )

    return Ok(EcopuckMessage(header, body))


def parse_parosci_pressure_message(line: str) -> Result[ParosciPressureMessage, str]:
    """Parses a message line as a Parosci pressure message."""
    pattern = re.compile(PAROSCI_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = ParosciPressureMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = ParosciPressureMessage.body_type(
        depth=float(match["depth"]),
    )

    return Ok(ParosciPressureMessage(header, body))


def parse_teledyne_dvl_message(line: str) -> Result[TeledyneDVLMessage, str]:
    """Parses a message line as a Teledyne DVL message."""

    pattern = re.compile(TELEDYNE_DVL_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header: TeledyneDVLMessage.header_type = TeledyneDVLMessage.header_type(
        topic=str(match["topic"]), timestamp=float(match["timestamp"])
    )

    body: TeledyneDVLMessage.body_type = TeledyneDVLMessage.body_type(
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
        dmg_x=float(match["dmg_x"]),
        dmg_y=float(match["dmg_y"]),
        dmg_z=float(match["dmg_z"]),
        course_over_ground=float(match["course_over_ground"]),
        speed_over_ground=float(match["speed_over_ground"]),
        true_heading=float(match["true_heading"]),
        gimbal_pitch=float(match["gimbal_pitch"]),
        sound_velocity=float(match["sound_velocity"]),
        bottom_track_status=int(match["bottom_track_status"]),
    )

    return Ok(TeledyneDVLMessage(header, body))


def parse_lq_modem_message(line: str) -> Result[TrackLinkModemMessage, str]:
    """Parses a message line as a LQ modem message."""

    pattern = re.compile(LQ_MODEM_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header: MessageHeader = TrackLinkModemMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = TrackLinkModemMessage.body_type(
        latitude=float(match["latitude"]),
        longitude=float(match["longitude"]),
        roll=float(match["roll"]),
        pitch=float(match["pitch"]),
        heading=float(match["heading"]),
        time=float(match["time"]),
        bearing=float(match["bearing"]),
        range=float(match["range"]),
    )

    return Ok(TrackLinkModemMessage(header, body))


def parse_evologics_modem_message(line: str) -> Result[EvologicsModemMessage, str]:
    """Parses a message line as an Evologics USBL message."""

    pattern = re.compile(EVOLOGICS_MODEM_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = EvologicsModemMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = EvologicsModemMessage.body_type(
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

    return Ok(EvologicsModemMessage(header, body))


def parse_micron_sonar_message(line: str) -> Result[MicronSonarMessage, str]:
    """Parses a message line as a Micron sonar message."""

    pattern = re.compile(MICRON_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = MicronSonarMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = MicronSonarMessage.body_type(
        profile_range=float(match["profile_range"]),
        profile_altitude=float(match["profile_altitude"]),
        pseudo_forward_distance=float(match["pseudo_forward_distance"]),
        angle=float(match["angle"]),
    )

    return Ok(MicronSonarMessage(header, body))


def parse_obstacle_avoidance_sonar_message(line: str) -> Result[OASonarMessage, str]:
    """Parses a message line as an OA sonar message."""

    pattern = re.compile(OAS_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = OASonarMessage.header_type(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    body = OASonarMessage.body_type(
        profile_range=float(match["profile_range"]),
        profile_altitude=float(match["profile_altitude"]),
        pseudo_forward_distance=float(match["pseudo_forward_distance"]),
    )

    return Ok(OASonarMessage(header, body))


BATTERY_TOPIC_TO_NAME: dict[str, str] = {
    "BATT": "battery",
    "BATT0": "battery_00",
    "BATT1": "battery_01",
    "BATT2": "battery_02",
}


def parse_battery_message(line: str) -> Result[BatteryMessage, str]:
    """Parses a message line as a BatteryMessage object."""

    pattern = re.compile(BATTERY_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = BatteryMessage.header_type(
        topic=str(match["topic"]), timestamp=float(match["timestamp"])
    )

    body = BatteryMessage.body_type(
        label=BATTERY_TOPIC_TO_NAME[header.topic],
        time_left=int(match["time_left"]),
        current=float(match["current"]),
        voltage=float(match["voltage"]),
        power=float(match["power"]),
        charge_percent=int(match["charge_percent"]),
        charging=bool(int(match["charging"])),
    )

    return Ok(BatteryMessage(header, body))


THRUSTER_TOPIC_TO_NAME: dict[str, str] = {
    "THR_PORT": "thruster_portside",
    "THR_STBD": "thruster_starboard",
    "THR_VERT": "thruster_vertical",
}


def parse_thruster_message(line: str) -> Result[ThrusterMessage, str]:
    """Parser function for thruster messages."""

    pattern = re.compile(THRUSTER_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse message line: {line}")

    header = ThrusterMessage.header_type(
        topic=str(match["topic"]), timestamp=float(match["timestamp"])
    )

    body = ThrusterMessage.body_type(
        label=THRUSTER_TOPIC_TO_NAME[header.topic],
        rpm=float(match["rpm"]),
        current=float(match["current"]),
        voltage=float(match["voltage"]),
        temperature=float(match["temperature"]),
    )

    return Ok(ThrusterMessage(header, body))


MESSAGE_PARSERS: list[MessageParser] = [
    parse_message_header,
    parse_image_message,
    parse_seabird_ctd_message,
    parse_aanderaa_ctd_message,
    parse_ecopuck_message,
    parse_parosci_pressure_message,
    parse_teledyne_dvl_message,
    parse_lq_modem_message,
    parse_evologics_modem_message,
    parse_micron_sonar_message,
    parse_obstacle_avoidance_sonar_message,
    parse_battery_message,
    parse_thruster_message,
]


MESSAGE_TYPE_TO_PARSER: dict[type, MessageParser] = {
    MessageHeader: parse_message_header,
    ImageCaptureMessage: parse_image_message,
    SeabirdCTDMessage: parse_seabird_ctd_message,
    AanderaaCTDMessage: parse_aanderaa_ctd_message,
    EcopuckMessage: parse_ecopuck_message,
    ParosciPressureMessage: parse_parosci_pressure_message,
    TeledyneDVLMessage: parse_teledyne_dvl_message,
    TrackLinkModemMessage: parse_lq_modem_message,
    EvologicsModemMessage: parse_evologics_modem_message,
    MicronSonarMessage: parse_micron_sonar_message,
    OASonarMessage: parse_obstacle_avoidance_sonar_message,
    BatteryMessage: parse_battery_message,
    ThrusterMessage: parse_thruster_message,
}


def get_message_parser(message_type: type) -> Optional[MessageParser]:
    """Returns a parser for the message type if the message type is within the
    set of messages, and none otherwise."""
    return MESSAGE_TYPE_TO_PARSER.get(message_type)
