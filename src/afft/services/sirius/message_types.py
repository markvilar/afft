"""Module for message classes."""

from dataclasses import dataclass


@dataclass
class AuvMessageHeader:
    """Class representing an AUV message header."""

    topic: str
    timestamp: float


@dataclass
class ImageCaptureData:
    """Class representing image capture data."""

    label: str
    filename: str
    trigger_time: float
    exposure_logged: bool
    exposure: int = 0


@dataclass
class SeabirdCTDData:
    """Class representing data from a Seabird CTD."""

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float


@dataclass
class AanderaaCTDData:
    """Class representing data from an Aanderaa CTD."""

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float


@dataclass
class EcopuckData:
    """Class representing data from an Ecopuck sensor."""

    chlorophyll: float
    backscatter: float
    cdom: float
    temperature: float


"""
Navigation system data types:
- ParosciPressureData
- TeledyneDVLData
- TrackLinkModemData
- EvologicsModemData
- MicronSonarData
- OASonarData

- TODO: GPS_RMC, GPS_GSV, MICRON_TRACE, MICRON_SECTOR
"""


@dataclass
class ParosciPressureData:
    """Class representing Parosci pressure data."""

    depth: float


@dataclass
class TeledyneDVLData:
    """Class representing Teledyne DVL data. Check documentation at:
    https://www.comm-tec.com/Docs/Manuali/RDI/WH_CG_Mar14.pdf"""

    altitude: float

    range_01: float
    range_02: float
    range_03: float
    range_04: float

    heading: float
    pitch: float
    roll: float

    velocity_x: float
    velocity_y: float
    velocity_z: float

    dmg_x: float
    dmg_y: float
    dmg_z: float

    course_over_ground: float
    speed_over_ground: float
    true_heading: float

    gimbal_pitch: float
    sound_velocity: float

    bottom_track_status: int


@dataclass
class TrackLinkModemData:
    """Class representing TrackLink modem data."""

    latitude: float
    longitude: float

    roll: float
    pitch: float
    heading: float

    time: float
    bearing: float
    range: float


@dataclass
class EvologicsModemData:
    """Class representing Evologics modem data."""

    target_latitude: float
    target_longitude: float
    target_depth: float

    target_x: float
    target_y: float
    target_z: float

    accuracy: float

    ship_latitude: float
    ship_longitude: float
    ship_roll: float
    ship_pitch: float
    ship_heading: float


@dataclass
class MicronSonarData:
    """Class representing Micron sonar data."""

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float
    angle: float


@dataclass
class OASonarData:
    """Class representing obstacle avoidance sonar data."""

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float


@dataclass
class BatteryData:
    """Class representing battery data."""

    label: str
    time_left: int
    current: float
    voltage: float
    power: float
    charge_percent: int
    charging: bool


@dataclass
class ThrusterData:
    """Class representing thruster data."""

    label: str
    rpm: float
    current: float
    voltage: float
    temperature: float


"""
AUV message types:
 - ImageCaptureMessage
 - SeabirdCTDMessage
 - AanderaaCTDMessage
 - EcopuckMessage
 - ParosciPressureMessage
 - TeledyneDVLMessage
 - TrackLinkModemMessage
 - EvologicsModemMessage
 - MicronSonarMessage
 - OASonarMessage
 - BatteryMessage
 - ThrusterMessage
"""


@dataclass
class ImageCaptureMessage:
    """Class representing an image capture message."""

    header_type = AuvMessageHeader
    body_type = ImageCaptureData

    header: AuvMessageHeader
    body: ImageCaptureData


@dataclass
class SeabirdCTDMessage:
    """Class representing a Seabird CTD message."""

    header_type = AuvMessageHeader
    body_type = SeabirdCTDData

    header: AuvMessageHeader
    body: SeabirdCTDData


@dataclass
class AanderaaCTDMessage:
    """Class representing an Aanderaa CTD message."""

    header_type = AuvMessageHeader
    body_type = AanderaaCTDData

    header: AuvMessageHeader
    body: AanderaaCTDData


@dataclass
class EcopuckMessage:
    """Class representing an Ecopuck message."""

    header_type = AuvMessageHeader
    body_type = EcopuckData

    header: AuvMessageHeader
    body: EcopuckData


@dataclass
class ParosciPressureMessage:
    """Class representing a Paroscientific pressure message."""

    header_type = AuvMessageHeader
    body_type = ParosciPressureData

    header: AuvMessageHeader
    body: ParosciPressureData


@dataclass
class TeledyneDVLMessage:
    """Class representing a Teledyne DVL message."""

    header_type = AuvMessageHeader
    body_type = TeledyneDVLData

    header: AuvMessageHeader
    body: TeledyneDVLData


@dataclass
class TrackLinkModemMessage:
    """Class representing a TrackLink modem message."""

    header_type = AuvMessageHeader
    body_type = TrackLinkModemData

    header: AuvMessageHeader
    body: TrackLinkModemData


@dataclass
class EvologicsModemMessage:
    """Class representing an Evologics modem message."""

    header_type = AuvMessageHeader
    body_type = EvologicsModemData

    header: AuvMessageHeader
    body: EvologicsModemData


@dataclass
class MicronSonarMessage:
    """Class representing a Micron sonar message."""

    header_type = AuvMessageHeader
    body_type = MicronSonarData

    header: AuvMessageHeader
    body: MicronSonarData


@dataclass
class OASonarMessage:
    """Class representing an OA sonar message."""

    header_type = AuvMessageHeader
    body_type = OASonarData

    header: AuvMessageHeader
    body: OASonarData


@dataclass
class BatteryMessage:
    """Class representing a battery message."""

    header_type = AuvMessageHeader
    body_type = BatteryData

    header: AuvMessageHeader
    body: BatteryData


@dataclass
class ThrusterMessage:
    """Class representing a thruster message."""

    header_type = AuvMessageHeader
    body_type = ThrusterData

    header: AuvMessageHeader
    body: ThrusterData


MESSAGE_TYPES: list[type] = [
    AuvMessageHeader,
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
]

MESSAGE_NAME_TO_TYPE: dict[str, type] = {type.__name__: type for type in MESSAGE_TYPES}