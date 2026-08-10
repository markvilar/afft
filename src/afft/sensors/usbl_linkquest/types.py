"""Types for the LinkQuest TrackLink 1500HA USBL sensor."""

import numpy as np

from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from scipy.spatial.transform import (
    RigidTransform,
    Rotation,
)


class TrackLinkFixLogEntry(BaseModel):
    """
    Parsed USBL_FIX entry from a TrackLink log file.

    Attributes
    ----------
    unix_timestamp: Unix timestamp in seconds.
    ship_latitude: Ship latitude in decimal degrees.
    ship_longitude: Ship longitude in decimal degrees.
    ship_heading: Ship heading in degrees from North, clockwise.
    ship_roll: Ship roll in degrees.
    ship_pitch: Ship pitch in degrees.
    target_bearing_angle: Bearing to target in degrees, relative to the
        transceiver frame (0 = forward, clockwise).
    target_slant_range: Slant range to target in metres.
    """

    model_config = ConfigDict(frozen=True)

    unix_timestamp: float
    ship_latitude: float
    ship_longitude: float
    ship_heading: float
    ship_roll: float
    ship_pitch: float
    target_bearing_angle: float
    target_slant_range: float


class TrackLinkRawLogEntry(BaseModel):
    """
    Parsed USBL_RAW entry from a TrackLink log file.

    X, Y, Z are the target offsets in metres in the physical sensor frame.
    The TrackLink log outputs X and Y swapped; the parser corrects this so
    that X = forward, Y = starboard, Z = down.

    Attributes
    ----------
    unix_timestamp: Unix timestamp in seconds.
    flag1: Integer flag preceding the time field. Absent on the first ping
        (None in that case).
    flag2: Integer flag following the time field.
    target_x: Target offset in metres along the forward direction.
    target_y: Target offset in metres along the starboard direction.
    target_z: Target offset in metres along the down direction (positive down).
    """

    model_config = ConfigDict(frozen=True)

    unix_timestamp: float
    flag1: int | None
    flag2: int
    target_x: float
    target_y: float
    target_z: float


class TrackLinkTransceiverExtrinsics(BaseModel):
    """
    Rigid-body extrinsics of the USBL transceiver in the ship body frame.

    The ship body frame has x pointing forward (bow), y pointing starboard,
    and z pointing down. Angles follow ZYX intrinsic Euler convention
    (yaw ψ, pitch θ, roll φ) with right-hand-positive rotations.

    Attributes
    ----------
    locx: Forward offset from ship reference point in metres.
    locy: Lateral offset in metres (positive starboard).
    locz: Vertical offset in metres (positive down).
    rotx: Roll in radians (positive: starboard down).
    roty: Pitch in radians (positive: bow up).
    rotz: Yaw in radians (positive clockwise viewed from above).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    locx: float = 0.0
    locy: float = 0.0
    locz: float = 0.0
    rotx: float = 0.0
    roty: float = 0.0
    rotz: float = 0.0

    @property
    def translation(self) -> NDArray[np.float64]:
        return np.array([self.locx, self.locy, self.locz], dtype=np.float64)

    @property
    def rotation(self) -> Rotation:
        return Rotation.from_euler(
            "zyx", [self.rotz, self.roty, self.rotx], degrees=False
        )

    @property
    def transform(self) -> RigidTransform:
        return RigidTransform.from_components(
            translation=self.translation,
            rotation=self.rotation,
        )


class TrackLinkResolvePositionFromMessagesConfig(BaseModel):
    """
    Configuration for the USBL position resolution step from AUV messages.

    The raw bearing is always treated as an azimuth in the transceiver body
    frame (0 = transceiver forward, clockwise). The full ZYX attitude chain
    (transceiver → ship body → NED) is applied on every call. Extrinsics are
    passed to the processor rather than configured here, since they are a
    property of the deployment.

    Attributes
    ----------
    timestamp_col: Name of the timestamp column in both DataFrames.
    bearing_col: Name of the bearing column in the USBL DataFrame.
    range_col: Name of the slant range column in the USBL DataFrame.
    ship_lat_col: Name of the ship latitude column.
    ship_lon_col: Name of the ship longitude column.
    ship_heading_col: Name of the ship heading column (degrees, clockwise from N).
    ship_roll_col: Name of the ship roll column (degrees).
    ship_pitch_col: Name of the ship pitch column (degrees).
    depth_col: Name of the depth column in the pressure DataFrame.
    max_time_gap_seconds: Maximum allowed gap between USBL and pressure windows.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp_col: str = "timestamp"
    bearing_col: str = "target_bearing_angle"
    range_col: str = "target_slant_range"
    ship_lat_col: str = "ship_latitude"
    ship_lon_col: str = "ship_longitude"
    ship_heading_col: str = "ship_heading"
    ship_roll_col: str = "ship_roll"
    ship_pitch_col: str = "ship_pitch"
    depth_col: str = "depth"
    max_time_gap_seconds: float = 60.0


class TrackLinkResolvePositionFromLogsConfig(BaseModel):
    """
    Configuration for the USBL position resolution step from log entries.

    Target XYZ in the sensor frame is taken directly from the log entries.
    The full ZYX attitude chain (transceiver → ship body → NED) is applied
    on every call. Extrinsics are passed to the processor rather than
    configured here, since they are a property of the deployment.

    Attributes
    ----------
    timestamp_col: Name of the timestamp column in the DataFrame.
    target_x_col: Name of the target X column (forward, sensor frame).
    target_y_col: Name of the target Y column (starboard, sensor frame).
    target_z_col: Name of the target Z column (down, sensor frame).
    bearing_col: Name of the bearing column in the USBL DataFrame.
    range_col: Name of the slant range column in the USBL DataFrame.
    ship_lat_col: Name of the ship latitude column.
    ship_lon_col: Name of the ship longitude column.
    ship_heading_col: Name of the ship heading column (degrees, clockwise from N).
    ship_roll_col: Name of the ship roll column (degrees).
    ship_pitch_col: Name of the ship pitch column (degrees).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp_col: str = "timestamp"
    target_x_col: str = "target_x"
    target_y_col: str = "target_y"
    target_z_col: str = "target_z"
    bearing_col: str = "target_bearing_angle"
    range_col: str = "target_slant_range"
    ship_lat_col: str = "ship_latitude"
    ship_lon_col: str = "ship_longitude"
    ship_heading_col: str = "ship_heading"
    ship_roll_col: str = "ship_roll"
    ship_pitch_col: str = "ship_pitch"


class TrackLinkUncertaintyConfig(BaseModel):
    """
    Deployment-calibrated uncertainty values for TrackLink USBL processing.

    Attributes
    ----------
    horizontal_position_std: 1σ horizontal position uncertainty in metres.
    depth_position_std: 1σ depth uncertainty in metres.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    horizontal_position_std: float = 15.8
    depth_position_std: float = 5.0


class TrackLinkProcessingFromMessagesConfig(BaseModel):
    """
    Combined configuration for the TrackLink USBL processing pipeline from AUV messages.

    Attributes
    ----------
    resolve: Configuration for position resolution from messages.
    uncertainty: Configuration for uncertainty estimation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    resolve: TrackLinkResolvePositionFromMessagesConfig = (
        TrackLinkResolvePositionFromMessagesConfig()
    )
    uncertainty: TrackLinkUncertaintyConfig = TrackLinkUncertaintyConfig()


class TrackLinkProcessingFromLogsConfig(BaseModel):
    """
    Combined configuration for the TrackLink USBL processing pipeline from log entries.

    Attributes
    ----------
    resolve: Configuration for position resolution from log entries.
    uncertainty: Configuration for uncertainty estimation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    resolve: TrackLinkResolvePositionFromLogsConfig = (
        TrackLinkResolvePositionFromLogsConfig()
    )
    uncertainty: TrackLinkUncertaintyConfig = TrackLinkUncertaintyConfig()
