"""Module for message classes."""

from dataclasses import dataclass
from typing import Optional, Self

from .message_interfaces import Message


@dataclass
class MessageHeader:
    """Class representing an AUV message header."""

    topic: str
    timestamp: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


@dataclass
class ImageCaptureData:
    """Class representing image capture data."""

    label: str
    filename: str
    trigger_time: float
    exposure_logged: bool
    exposure: int = 0

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


@dataclass
class SeabirdCTDData:
    """Class representing data from a Seabird CTD."""

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


@dataclass
class AanderaaCTDData:
    """Class representing data from an Aanderaa CTD."""

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


@dataclass
class EcopuckData:
    """Class representing data from an Ecopuck sensor."""

    chlorophyll: float
    backscatter: float
    cdom: float
    temperature: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


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

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


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

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


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

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return self.__dict__


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

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return {
            "target_latitude": self.target_latitude,
            "target_longitude": self.target_longitude,
            "target_depth": self.target_depth,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "target_z": self.target_z,
            "accuracy": self.accuracy,
            "ship_latitude": self.ship_latitude,
            "ship_longitude": self.ship_longitude,
            "ship_roll": self.ship_roll,
            "ship_pitch": self.ship_pitch,
            "ship_heading": self.ship_heading,
        }


@dataclass
class MicronSonarData:
    """Class representing Micron sonar data."""

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float
    angle: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return {
            "profile_range": self.profile_range,
            "profile_altitude": self.profile_altitude,
            "pseudo_forward_distance": self.pseudo_forward_distance,
            "angle": self.angle,
        }


@dataclass
class OASonarData:
    """Class representing obstacle avoidance sonar data."""

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return {
            "profile_range": self.profile_range,
            "profile_altitude": self.profile_altitude,
            "pseudo_forward_distance": self.pseudo_forward_distance,
        }


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

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return {
            "label": self.label,
            "time_left": self.time_left,
            "current": self.current,
            "voltage": self.voltage,
            "power": self.power,
            "charge_percent": self.charge_percent,
            "charging": self.charging,
        }


@dataclass
class ThrusterData:
    """Class representing thruster data."""

    label: str
    rpm: float
    current: float
    voltage: float
    temperature: float

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        return {
            "label": self.label,
            "rpm": self.rpm,
            "current": self.current,
            "voltage": self.voltage,
            "temperature": self.temperature,
        }


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

    header_type = MessageHeader
    body_type = ImageCaptureData

    header: MessageHeader
    body: ImageCaptureData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class SeabirdCTDMessage:
    """Class representing a Seabird CTD message."""

    header_type = MessageHeader
    body_type = SeabirdCTDData

    header: MessageHeader
    body: SeabirdCTDData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class AanderaaCTDMessage:
    """Class representing an Aanderaa CTD message."""

    header_type = MessageHeader
    body_type = AanderaaCTDData

    header: MessageHeader
    body: AanderaaCTDData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class EcopuckMessage:
    """Class representing an Ecopuck message."""

    header_type = MessageHeader
    body_type = EcopuckData

    header: MessageHeader
    body: EcopuckData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class ParosciPressureMessage:
    """Class representing a Paroscientific pressure message."""

    header_type = MessageHeader
    body_type = ParosciPressureData

    header: MessageHeader
    body: ParosciPressureData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class TeledyneDVLMessage:
    """Class representing a Teledyne DVL message."""

    header_type = MessageHeader
    body_type = TeledyneDVLData

    header: MessageHeader
    body: TeledyneDVLData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class TrackLinkModemMessage:
    """Class representing a TrackLink modem message."""

    header_type = MessageHeader
    body_type = TrackLinkModemData

    header: MessageHeader
    body: TrackLinkModemData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class EvologicsModemMessage:
    """Class representing an Evologics modem message."""

    header_type = MessageHeader
    body_type = EvologicsModemData

    header: MessageHeader
    body: EvologicsModemData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class MicronSonarMessage:
    """Class representing a Micron sonar message."""

    header_type = MessageHeader
    body_type = MicronSonarData

    header: MessageHeader
    body: MicronSonarData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class OASonarMessage:
    """Class representing an OA sonar message."""

    header_type = MessageHeader
    body_type = OASonarData

    header: MessageHeader
    body: OASonarData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class BatteryMessage:
    """Class representing a battery message."""

    header_type = MessageHeader
    body_type = BatteryData

    header: MessageHeader
    body: BatteryData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


@dataclass
class ThrusterMessage:
    """Class representing a thruster message."""

    header_type = MessageHeader
    body_type = ThrusterData

    header: MessageHeader
    body: ThrusterData

    def to_dict(self: Self) -> dict:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.body.to_dict())
        return data


# Collection of message types to simplify imports
MessageTypes: list[Message] = [
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


MESSAGE_NAME_TO_TYPE: dict[str, type] = {type.__name__: type for type in MessageTypes}


def message_name_to_type(name: str) -> Optional[type]:
    """Returns a message type if the name is a valid message name, and none otherwise."""
    return MESSAGE_NAME_TO_TYPE.get(name)
