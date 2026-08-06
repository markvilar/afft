"""Module for message classes."""

from datetime import datetime
from typing import Any, Optional, Self

from pydantic import BaseModel, ConfigDict


class MessageHeader(BaseModel):
    """
    Class representing an AUV message header.

    Attributes
    ----------
    topic: Message topic string.
    timestamp: Message timestamp.
    """

    model_config = ConfigDict(frozen=True)

    topic: str
    timestamp: datetime

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class ImageCaptureMessagePayloadV1(BaseModel):
    """
    Payload of an image capture message.

    Attributes
    ----------
    label: Image identifier.
    filename: Image filename.
    trigger_time: Camera trigger time.
    exposure_logged: Whether an exposure value was logged.
    exposure: Camera exposure value.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    filename: str
    trigger_time: datetime
    exposure_logged: bool
    exposure: int = 0

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class SeabirdCTDMessagePayloadV1(BaseModel):
    """
    Payload of a Seabird CTD message.

    Attributes
    ----------
    conductivity: Water conductivity.
    temperature: Water temperature.
    salinity: Water salinity.
    pressure: Water pressure.
    sound_velocity: Speed of sound in water.
    """

    model_config = ConfigDict(frozen=True)

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class AanderaaCTDMessagePayloadV1(BaseModel):
    """
    Payload of an Aanderaa CTD message.

    Attributes
    ----------
    conductivity: Water conductivity.
    temperature: Water temperature.
    salinity: Water salinity.
    pressure: Water pressure.
    sound_velocity: Speed of sound in water.
    """

    model_config = ConfigDict(frozen=True)

    conductivity: float
    temperature: float
    salinity: float
    pressure: float
    sound_velocity: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class EcopuckMessagePayloadV1(BaseModel):
    """
    Payload of an Ecopuck message.

    Attributes
    ----------
    chlorophyll: Chlorophyll concentration.
    backscatter: Optical backscatter.
    cdom: Colored dissolved organic matter.
    temperature: Water temperature.
    """

    model_config = ConfigDict(frozen=True)

    chlorophyll: float
    backscatter: float
    cdom: float
    temperature: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


"""
Navigation system payload types:
- ParosciPressureMessagePayloadV1
- TeledyneDVLMessagePayloadV1
- TrackLinkModemMessagePayloadV1
- EvologicsModemMessagePayloadV1
- MicronSonarMessagePayloadV1
- OASonarMessagePayloadV1
- GpsGsvMessagePayloadV1
- GpsRmcMessagePayloadV1

- TODO: MICRON_TRACE, MICRON_SECTOR
"""


class ParosciPressureMessagePayloadV1(BaseModel):
    """
    Payload of a Parosci pressure message.

    Attributes
    ----------
    depth: Water depth.
    """

    model_config = ConfigDict(frozen=True)

    depth: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class TeledyneDVLMessagePayloadV1(BaseModel):
    """
    Payload of a Teledyne DVL message. Check documentation at:
    https://www.comm-tec.com/Docs/Manuali/RDI/WH_CG_Mar14.pdf

    Attributes
    ----------
    altitude: Altitude above the seabed.
    range_01: Beam 1 range.
    range_02: Beam 2 range.
    range_03: Beam 3 range.
    range_04: Beam 4 range.
    heading: Vehicle heading.
    pitch: Vehicle pitch.
    roll: Vehicle roll.
    velocity_x: Velocity along x.
    velocity_y: Velocity along y.
    velocity_z: Velocity along z.
    dmg_x: Distance made good along x.
    dmg_y: Distance made good along y.
    dmg_z: Distance made good along z.
    course_over_ground: Course over ground.
    speed_over_ground: Speed over ground.
    true_heading: True heading.
    gimbal_pitch: Gimbal pitch.
    sound_velocity: Speed of sound in water.
    bottom_track_status: Bottom track status flag.
    """

    model_config = ConfigDict(frozen=True)

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

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class TrackLinkModemMessagePayloadV1(BaseModel):
    """
    Payload of a TrackLink modem message.

    Attributes
    ----------
    ship_latitude: Ship latitude.
    ship_longitude: Ship longitude.
    ship_roll: Ship roll.
    ship_pitch: Ship pitch.
    ship_heading: Ship heading.
    device_time: Modem device time.
    target_bearing_angle: Bearing angle to target.
    target_slant_range: Slant range to target.
    """

    model_config = ConfigDict(frozen=True)

    ship_latitude: float
    ship_longitude: float

    ship_roll: float
    ship_pitch: float
    ship_heading: float

    device_time: float
    target_bearing_angle: float
    target_slant_range: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class EvologicsModemMessagePayloadV1(BaseModel):
    """
    Payload of an Evologics modem message.

    Attributes
    ----------
    target_latitude: Target latitude.
    target_longitude: Target longitude.
    target_depth: Target depth.
    target_x: Target x position.
    target_y: Target y position.
    target_z: Target z position.
    accuracy: Fix accuracy.
    ship_latitude: Ship latitude.
    ship_longitude: Ship longitude.
    ship_roll: Ship roll.
    ship_pitch: Ship pitch.
    ship_heading: Ship heading.
    """

    model_config = ConfigDict(frozen=True)

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

    def to_dict(self: Self) -> dict[str, Any]:
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


class MicronSonarMessagePayloadV1(BaseModel):
    """
    Payload of a Micron sonar message.

    Attributes
    ----------
    profile_range: Sonar profile range.
    profile_altitude: Sonar profile altitude.
    pseudo_forward_distance: Pseudo forward distance.
    angle: Sonar head angle.
    """

    model_config = ConfigDict(frozen=True)

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float
    angle: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return {
            "profile_range": self.profile_range,
            "profile_altitude": self.profile_altitude,
            "pseudo_forward_distance": self.pseudo_forward_distance,
            "angle": self.angle,
        }


class OASonarMessagePayloadV1(BaseModel):
    """
    Payload of an obstacle avoidance sonar message.

    Attributes
    ----------
    profile_range: Sonar profile range.
    profile_altitude: Sonar profile altitude.
    pseudo_forward_distance: Pseudo forward distance.
    """

    model_config = ConfigDict(frozen=True)

    profile_range: float
    profile_altitude: float
    pseudo_forward_distance: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return {
            "profile_range": self.profile_range,
            "profile_altitude": self.profile_altitude,
            "pseudo_forward_distance": self.pseudo_forward_distance,
        }


class GpsGsvMessagePayloadV1(BaseModel):
    """
    Payload of a GPS satellites-in-view message (GPGSV).

    Attributes
    ----------
    satellites_in_view: Number of satellites in view.
    """

    model_config = ConfigDict(frozen=True)

    satellites_in_view: int

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class GpsRmcMessagePayloadV1(BaseModel):
    """
    Payload of a GPS recommended minimum navigation message (GPRMC).

    Attributes
    ----------
    latitude: Latitude.
    longitude: Longitude.
    bad: Bad fix flag.
    status: Fix status.
    speed_knots: Speed over ground in knots.
    course_over_ground: Course over ground.
    magnetic_variation: Magnetic variation.
    """

    model_config = ConfigDict(frozen=True)

    latitude: float
    longitude: float
    bad: int
    status: str
    speed_knots: float
    course_over_ground: float
    magnetic_variation: float

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        return self.model_dump()


class BatteryMessagePayloadV1(BaseModel):
    """
    Payload of a battery message.

    Attributes
    ----------
    label: Battery identifier.
    time_left: Estimated time left.
    current: Battery current.
    voltage: Battery voltage.
    power: Battery power.
    charge_percent: Battery charge percentage.
    charging: Whether the battery is charging.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    time_left: int
    current: float
    voltage: float
    power: float
    charge_percent: int
    charging: bool

    def to_dict(self: Self) -> dict[str, Any]:
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


class ThrusterMessagePayloadV1(BaseModel):
    """
    Payload of a thruster message.

    Attributes
    ----------
    label: Thruster identifier.
    rpm: Thruster shaft speed.
    current: Motor current draw.
    voltage: Motor supply voltage.
    temperature: Motor temperature.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    rpm: float
    current: float
    voltage: float
    temperature: float

    def to_dict(self: Self) -> dict[str, Any]:
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
 - ImageCaptureMessageV1
 - SeabirdCTDMessageV1
 - AanderaaCTDMessageV1
 - EcopuckMessageV1
 - ParosciPressureMessageV1
 - TeledyneDVLMessageV1
 - TrackLinkModemMessageV1
 - EvologicsModemMessageV1
 - MicronSonarMessageV1
 - OASonarMessageV1
 - GpsGsvMessageV1
 - GpsRmcMessageV1
 - BatteryMessageV1
 - ThrusterMessageV1
"""


class ImageCaptureMessageV1(BaseModel):
    """
    An image capture message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: ImageCaptureMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class SeabirdCTDMessageV1(BaseModel):
    """
    A Seabird CTD message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: SeabirdCTDMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class AanderaaCTDMessageV1(BaseModel):
    """
    An Aanderaa CTD message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: AanderaaCTDMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class EcopuckMessageV1(BaseModel):
    """
    An Ecopuck message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: EcopuckMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class ParosciPressureMessageV1(BaseModel):
    """
    A Paroscientific pressure message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: ParosciPressureMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class TeledyneDVLMessageV1(BaseModel):
    """
    A Teledyne DVL message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: TeledyneDVLMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class TrackLinkModemMessageV1(BaseModel):
    """
    A TrackLink modem message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: TrackLinkModemMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class EvologicsModemMessageV1(BaseModel):
    """
    An Evologics modem message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: EvologicsModemMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class MicronSonarMessageV1(BaseModel):
    """
    A Micron sonar message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: MicronSonarMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class OASonarMessageV1(BaseModel):
    """
    An OA sonar message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: OASonarMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class GpsGsvMessageV1(BaseModel):
    """
    A GPS satellites-in-view message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: GpsGsvMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class GpsRmcMessageV1(BaseModel):
    """
    A GPS recommended minimum navigation message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: GpsRmcMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class BatteryMessageV1(BaseModel):
    """
    A battery message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: BatteryMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


class ThrusterMessageV1(BaseModel):
    """
    A thruster message.

    Attributes
    ----------
    header: Message header.
    payload: Message payload.
    """

    model_config = ConfigDict(frozen=True)

    header: MessageHeader
    payload: ThrusterMessagePayloadV1

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dict representation of the object."""
        data = self.header.to_dict()
        data.update(self.payload.to_dict())
        return data


MESSAGE_TYPES: list[type] = [
    ImageCaptureMessageV1,
    SeabirdCTDMessageV1,
    AanderaaCTDMessageV1,
    EcopuckMessageV1,
    ParosciPressureMessageV1,
    TeledyneDVLMessageV1,
    TrackLinkModemMessageV1,
    EvologicsModemMessageV1,
    MicronSonarMessageV1,
    OASonarMessageV1,
    GpsGsvMessageV1,
    GpsRmcMessageV1,
    BatteryMessageV1,
    ThrusterMessageV1,
]


MESSAGE_NAME_TO_TYPE: dict[str, type] = {
    message_type.__name__: message_type for message_type in MESSAGE_TYPES
}


def get_message_type(name: str) -> Optional[type]:
    """Returns a message type if the name is a valid message name, and none otherwise."""
    return MESSAGE_NAME_TO_TYPE.get(name)
