"""Module for message data classes."""

from dataclasses import dataclass


@dataclass
class AuvMessageHeader:
    """Class representing an AUV message header."""

    topic: str
    timestamp: float


@dataclass
class ImageCaptureDataV1:
    """Class representing an image message."""

    trigger_time: float
    label: str


@dataclass
class ImageCaptureDataV2:
    """Class representing image version 2, with logged exposure values."""

    trigger_time: float
    label: str
    exposure: int


"""
Navigation system data types:
- LQModemData
- EvologicsData
- TODO: RDI, PAROSCI, GPS_RMC, GPS_GSV, OAS, MICRON, MICRON_RETURNS, MICRON_TRACE, MICRON_SECTOR
"""

@dataclass
class TeledyneDVLData:
    """Class representing Teledyne DVL data.
    Check documentation at: https://www.comm-tec.com/Docs/Manuali/RDI/WH_CG_Mar14.pdf
    """

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

    position_x: float
    position_y: float
    position_z: float

    course_over_ground: float
    speed_over_ground: float
    true_heading: float
    
    gimbal_pitch: float
    sound_velocity: float

    bottom_track_status: int


@dataclass
class LQModemData:
    """Class representing LQ modem data."""

    latitude: float
    longitude: float

    roll: float
    pitch: float
    heading: float

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


"""
Power system data types:
- BatteryData
- ThrusterData
"""


@dataclass
class BatteryData:
    """Class representing battery data."""

    name: str
    time_left: int
    current: float
    voltage: float
    power: float
    charge_percent: int
    charging: bool


@dataclass
class ThrusterData:
    """Class representing thruster data."""

    name: str
    rpm: float
    current: float
    voltage: float
    temperature: float
