"""Module for parsing of message data types."""

import re

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .message_interfaces import MessageParseError, MessageParser
from .message_types import (
    MessageHeader,
    ImageCaptureMessageV1,
    ImageCaptureMessagePayloadV1,
    SeabirdCTDMessageV1,
    SeabirdCTDMessagePayloadV1,
    AanderaaCTDMessageV1,
    AanderaaCTDMessagePayloadV1,
    EcopuckMessageV1,
    EcopuckMessagePayloadV1,
    ParosciPressureMessageV1,
    ParosciPressureMessagePayloadV1,
    TeledyneDVLMessageV1,
    TeledyneDVLMessagePayloadV1,
    TrackLinkModemMessageV1,
    TrackLinkModemMessagePayloadV1,
    EvologicsModemMessageV1,
    EvologicsModemMessagePayloadV1,
    MicronSonarMessageV1,
    MicronSonarMessagePayloadV1,
    OASonarMessageV1,
    OASonarMessagePayloadV1,
    GpsGsvMessageV1,
    GpsGsvMessagePayloadV1,
    GpsRmcMessageV1,
    GpsRmcMessagePayloadV1,
    BatteryMessageV1,
    BatteryMessagePayloadV1,
    ThrusterMessageV1,
    ThrusterMessagePayloadV1,
)


MESSAGE_HEADER_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+).*   # unlimited of any character after timestamp
    $
    """

IMAGE_CAPTURE_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    (\[(?P<trigger_time>\d+.\d+)\])\s+
    (?P<filename>[\w]+\.[\w]+)\s*       # Zero or unlimited since next group is optional
    (exp:\s+(?P<exposure>\d+))?\s*      # Optional exposure group
    $
    """

SEABIRD_CTD_V1_REGEX = r"""
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

AANDERAA_CTD_V1_REGEX = r"""
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

ECOPUCK_V1_REGEX = r"""
    ^
    (?P<topic>\w+):\s+
    (?P<timestamp>[-+]?\d+\.\d+)\s+
    chlor:(?P<chlorophyll>[-+]?\d+\.\d+)\s+
    bcksct:(?P<backscatter>[-+]?\d+\.\d+)\s+
    cdom:(?P<cdom>[-+]?\d+\.\d+)\s+
    temp:(?P<temperature>[-+]?\d+\.\d+)\s*
    $
    """

PAROSCI_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    (?P<depth>[-+]?\d+\.\d+)\s*
    $
    """

TELEDYNE_DVL_V1_REGEX = r"""
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

LQ_MODEM_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    time:\s*(?P<device_time>[-+]?\d*[.]\d*)\s+
    Lat:\s*(?P<ship_latitude>[-+]?\d*[.]\d*)\s+
    Lon:\s*(?P<ship_longitude>[-+]?\d*[.]\d*)\s+
    hdg:\s*(?P<ship_heading>[-+]?\d*[.]\d*)\s+
    roll:\s*(?P<ship_roll>[-+]?\d*[.]\d*)\s+
    pitch:\s*(?P<ship_pitch>[-+]?\d*[.]\d*)\s+
    bear:\s*(?P<target_bearing_angle>[-+]?\d*[.]\d*)\s+
    rng:\s*(?P<target_slant_range>[-+]?\d*[.]\d*)\s*
    $
    """

EVOLOGICS_MODEM_V1_REGEX = r"""
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

MICRON_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    ProfRng:\s*(?P<profile_range>[-+]?\d+\.\d+)\s+
    PseudoAlt:\s*(?P<profile_altitude>[-+]?\d+\.\d+)\s+
    PseudoFwdDistance:\s*(?P<pseudo_forward_distance>[-+]?\d+\.\d+)\s+
    Angle:\s*(?P<angle>[-+]?\d+\.\d+).*
    $
    """

OAS_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    ProfRng:\s*(?P<profile_range>[-+]?\d+\.\d+)\s+
    PseudoAlt:\s*(?P<profile_altitude>[-+]?\d+\.\d+)\s+
    PseudoFwdDistance:\s*(?P<pseudo_forward_distance>[-+]?\d+\.\d+).*
    $
    """

THRUSTER_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    RPM:\s*(?P<rpm>[-+]?\d*[.]\d*)\s+
    A:\s*(?P<current>[-+]?\d*[.]\d*)\s+
    V:\s*(?P<voltage>[-+]?\d*[.]\d*)\s+
    T:\s*(?P<temperature>[-+]?\d*[.]\d*)\s*
    $
    """

GPS_GSV_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    SV:(?P<satellites_in_view>\d+)\s*
    $
    """

GPS_RMC_V1_REGEX = r"""
    ^
    (?P<topic>.+?):\s+
    (?P<timestamp>\d+\.\d+)\s+
    Lat:(?P<latitude>[-+]?\d+\.\d+)\s+[NS]\s+
    Lon:(?P<longitude>[-+]?\d+\.\d+)\s+[EW]\s+
    Bad:\s*(?P<bad>\d+)\s+
    (?P<status>[AV])\s+
    Spd:(?P<speed>[-+]?\d+\.\d+)\s+
    Crs:(?P<course>[-+]?\d+\.\d+)\s+
    Mg:(?P<magnetic_variation>[-+]?\d+\.\d+)\s*
    $
    """

BATTERY_V1_REGEX = r"""
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


def _unix_epoch_to_datetime(ts: float) -> datetime:
    """Convert a Unix float timestamp (seconds) to a UTC datetime object."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def parse_message_header(line: str) -> MessageHeader:
    """Parses the header from a message line."""

    pattern = re.compile(MESSAGE_HEADER_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse header: {line}")

    try:
        return MessageHeader(
            topic=match["topic"],
            timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
        )
    except ValidationError as error:
        raise MessageParseError(f"failed to parse header: {line}") from error


def parse_image_message_v1(line: str) -> ImageCaptureMessageV1:
    """Parses a message line as an image capture message."""

    pattern = re.compile(IMAGE_CAPTURE_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse image message: {line}")

    exposure_logged: bool = match["exposure"] is not None

    try:
        return ImageCaptureMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=ImageCaptureMessagePayloadV1(
                label=Path(match["filename"]).stem,
                filename=match["filename"],
                trigger_time=_unix_epoch_to_datetime(
                    float(match["trigger_time"])
                ),
                exposure_logged=exposure_logged,
                exposure=match["exposure"] if exposure_logged else 0,
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse image message: {line}"
        ) from error


def parse_seabird_ctd_message_v1(line: str) -> SeabirdCTDMessageV1:
    """Parses a message line as a Seabird CTD message."""

    pattern = re.compile(SEABIRD_CTD_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse Seabird CTD message: {line}")

    try:
        return SeabirdCTDMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=SeabirdCTDMessagePayloadV1(
                conductivity=match["conductivity"],
                temperature=match["temperature"],
                salinity=match["salinity"],
                pressure=match["pressure"],
                sound_velocity=match["sound_velocity"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse Seabird CTD message: {line}"
        ) from error


def parse_aanderaa_ctd_message_v1(line: str) -> AanderaaCTDMessageV1:
    """Parses a message line as an Aanderaa CTD message."""

    pattern = re.compile(AANDERAA_CTD_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse Aanderaa CTD message: {line}")

    try:
        return AanderaaCTDMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=AanderaaCTDMessagePayloadV1(
                conductivity=match["conductivity"],
                temperature=match["temperature"],
                salinity=match["salinity"],
                pressure=match["pressure"],
                sound_velocity=match["sound_velocity"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse Aanderaa CTD message: {line}"
        ) from error


def parse_ecopuck_message_v1(line: str) -> EcopuckMessageV1:
    """Parses a message line as an Ecopuck water quality message."""

    pattern = re.compile(ECOPUCK_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse Ecopuck message: {line}")

    try:
        return EcopuckMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=EcopuckMessagePayloadV1(
                chlorophyll=match["chlorophyll"],
                backscatter=match["backscatter"],
                cdom=match["cdom"],
                temperature=match["temperature"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse Ecopuck message: {line}"
        ) from error


def parse_parosci_pressure_message_v1(line: str) -> ParosciPressureMessageV1:
    """Parses a message line as a Parosci pressure message."""
    pattern = re.compile(PAROSCI_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return ParosciPressureMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=ParosciPressureMessagePayloadV1(depth=match["depth"]),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_teledyne_dvl_message_v1(line: str) -> TeledyneDVLMessageV1:
    """Parses a message line as a Teledyne DVL message."""

    pattern = re.compile(TELEDYNE_DVL_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return TeledyneDVLMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=TeledyneDVLMessagePayloadV1(
                altitude=match["altitude"],
                range_01=match["range_01"],
                range_02=match["range_02"],
                range_03=match["range_03"],
                range_04=match["range_04"],
                heading=match["heading"],
                pitch=match["pitch"],
                roll=match["roll"],
                velocity_x=match["velocity_x"],
                velocity_y=match["velocity_y"],
                velocity_z=match["velocity_z"],
                dmg_x=match["dmg_x"],
                dmg_y=match["dmg_y"],
                dmg_z=match["dmg_z"],
                course_over_ground=match["course_over_ground"],
                speed_over_ground=match["speed_over_ground"],
                true_heading=match["true_heading"],
                gimbal_pitch=match["gimbal_pitch"],
                sound_velocity=match["sound_velocity"],
                bottom_track_status=match["bottom_track_status"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_lq_modem_message_v1(line: str) -> TrackLinkModemMessageV1:
    """Parses a message line as a LQ modem message."""

    pattern = re.compile(LQ_MODEM_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return TrackLinkModemMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=TrackLinkModemMessagePayloadV1(
                ship_latitude=match["ship_latitude"],
                ship_longitude=match["ship_longitude"],
                ship_roll=match["ship_roll"],
                ship_pitch=match["ship_pitch"],
                ship_heading=match["ship_heading"],
                device_time=match["device_time"],
                target_bearing_angle=match["target_bearing_angle"],
                target_slant_range=match["target_slant_range"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_evologics_modem_message_v1(line: str) -> EvologicsModemMessageV1:
    """Parses a message line as an Evologics USBL message."""

    pattern = re.compile(EVOLOGICS_MODEM_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return EvologicsModemMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=EvologicsModemMessagePayloadV1(
                target_latitude=match["target_latitude"],
                target_longitude=match["target_longitude"],
                target_depth=match["target_depth"],
                target_x=match["target_x"],
                target_y=match["target_y"],
                target_z=match["target_z"],
                accuracy=match["accuracy"],
                ship_latitude=match["ship_latitude"],
                ship_longitude=match["ship_longitude"],
                ship_roll=match["ship_roll"],
                ship_pitch=match["ship_pitch"],
                ship_heading=match["ship_heading"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_micron_sonar_message_v1(line: str) -> MicronSonarMessageV1:
    """Parses a message line as a Micron sonar message."""

    pattern = re.compile(MICRON_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return MicronSonarMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=MicronSonarMessagePayloadV1(
                profile_range=match["profile_range"],
                profile_altitude=match["profile_altitude"],
                pseudo_forward_distance=match["pseudo_forward_distance"],
                angle=match["angle"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_obstacle_avoidance_sonar_message_v1(line: str) -> OASonarMessageV1:
    """Parses a message line as an OA sonar message."""

    pattern = re.compile(OAS_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return OASonarMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=OASonarMessagePayloadV1(
                profile_range=match["profile_range"],
                profile_altitude=match["profile_altitude"],
                pseudo_forward_distance=match["pseudo_forward_distance"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


def parse_gps_gsv_message_v1(line: str) -> GpsGsvMessageV1:
    """Parses a message line as a GPS satellites-in-view message."""

    pattern = re.compile(GPS_GSV_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse GPS GSV message: {line}")

    try:
        return GpsGsvMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=GpsGsvMessagePayloadV1(
                satellites_in_view=match["satellites_in_view"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse GPS GSV message: {line}"
        ) from error


def parse_gps_rmc_message_v1(line: str) -> GpsRmcMessageV1:
    """Parses a message line as a GPS recommended minimum navigation message."""

    pattern = re.compile(GPS_RMC_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse GPS RMC message: {line}")

    try:
        return GpsRmcMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=GpsRmcMessagePayloadV1(
                latitude=match["latitude"],
                longitude=match["longitude"],
                bad=match["bad"],
                status=match["status"],
                speed_knots=match["speed"],
                course_over_ground=match["course"],
                magnetic_variation=match["magnetic_variation"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse GPS RMC message: {line}"
        ) from error


BATTERY_TOPIC_TO_NAME: dict[str, str] = {
    "BATT": "battery",
    "BATT0": "battery_00",
    "BATT1": "battery_01",
    "BATT2": "battery_02",
}


def parse_battery_message_v1(line: str) -> BatteryMessageV1:
    """Parses a message line as a BatteryMessageV1 object."""

    pattern = re.compile(BATTERY_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return BatteryMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=BatteryMessagePayloadV1(
                label=BATTERY_TOPIC_TO_NAME[match["topic"]],
                time_left=match["time_left"],
                current=match["current"],
                voltage=match["voltage"],
                power=match["power"],
                charge_percent=match["charge_percent"],
                charging=bool(int(match["charging"])),
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


THRUSTER_TOPIC_TO_NAME: dict[str, str] = {
    "THR_PORT": "thruster_portside",
    "THR_STBD": "thruster_starboard",
    "THR_VERT": "thruster_vertical",
}


def parse_thruster_message_v1(line: str) -> ThrusterMessageV1:
    """Parser function for thruster messages."""

    pattern = re.compile(THRUSTER_V1_REGEX, re.VERBOSE)
    match = pattern.match(line)

    if not match:
        raise MessageParseError(f"failed to parse message line: {line}")

    try:
        return ThrusterMessageV1(
            header=MessageHeader(
                topic=match["topic"],
                timestamp=_unix_epoch_to_datetime(float(match["timestamp"])),
            ),
            payload=ThrusterMessagePayloadV1(
                label=THRUSTER_TOPIC_TO_NAME[match["topic"]],
                rpm=match["rpm"],
                current=match["current"],
                voltage=match["voltage"],
                temperature=match["temperature"],
            ),
        )
    except ValidationError as error:
        raise MessageParseError(
            f"failed to parse message line: {line}"
        ) from error


MESSAGE_PARSERS: list[MessageParser] = [
    parse_image_message_v1,
    parse_seabird_ctd_message_v1,
    parse_aanderaa_ctd_message_v1,
    parse_ecopuck_message_v1,
    parse_parosci_pressure_message_v1,
    parse_teledyne_dvl_message_v1,
    parse_lq_modem_message_v1,
    parse_evologics_modem_message_v1,
    parse_micron_sonar_message_v1,
    parse_obstacle_avoidance_sonar_message_v1,
    parse_gps_gsv_message_v1,
    parse_gps_rmc_message_v1,
    parse_battery_message_v1,
    parse_thruster_message_v1,
]


MESSAGE_TYPE_TO_PARSER: dict[type, MessageParser] = {
    ImageCaptureMessageV1: parse_image_message_v1,
    SeabirdCTDMessageV1: parse_seabird_ctd_message_v1,
    AanderaaCTDMessageV1: parse_aanderaa_ctd_message_v1,
    EcopuckMessageV1: parse_ecopuck_message_v1,
    ParosciPressureMessageV1: parse_parosci_pressure_message_v1,
    TeledyneDVLMessageV1: parse_teledyne_dvl_message_v1,
    TrackLinkModemMessageV1: parse_lq_modem_message_v1,
    EvologicsModemMessageV1: parse_evologics_modem_message_v1,
    MicronSonarMessageV1: parse_micron_sonar_message_v1,
    OASonarMessageV1: parse_obstacle_avoidance_sonar_message_v1,
    GpsGsvMessageV1: parse_gps_gsv_message_v1,
    GpsRmcMessageV1: parse_gps_rmc_message_v1,
    BatteryMessageV1: parse_battery_message_v1,
    ThrusterMessageV1: parse_thruster_message_v1,
}


def get_message_parser(message_type: type) -> Optional[MessageParser]:
    """Returns a parser for the message type if the message type is within the
    set of messages, and none otherwise."""
    return MESSAGE_TYPE_TO_PARSER.get(message_type)
