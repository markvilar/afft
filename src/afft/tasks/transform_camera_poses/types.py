"""Data types for the transform camera poses task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class CameraVehicleExtrinsics:
    """
    Rigid-body extrinsics of the stereo camera in the vehicle body frame.

    Coordinate convention follows SNAME: posx is forward (bow), posy is
    starboard, posz is downward. Rotation angles follow ZYX intrinsic Euler
    convention (rotz=yaw, roty=pitch, rotx=roll) and are expressed in degrees.

    Attributes
    ----------
    posx: Forward offset from vehicle reference point in metres.
    posy: Lateral offset in metres (positive starboard).
    posz: Vertical offset in metres (positive downward).
    rotx: Roll in degrees (positive: starboard down).
    roty: Pitch in degrees (positive: bow up).
    rotz: Yaw in degrees (positive clockwise viewed from above).
    """

    posx: float = 0.0
    posy: float = 0.0
    posz: float = 0.0
    rotx: float = 0.0
    roty: float = 0.0
    rotz: float = 0.0


@dataclass(slots=True, frozen=True)
class TransformCameraPosesConfig:
    """
    Column configuration for the transform camera poses task.

    Attributes
    ----------
    latitude_column: Latitude column in the input camera pose frame.
    longitude_column: Longitude column in the input camera pose frame.
    heading_column: Vehicle heading column in degrees, clockwise from North.
    pitch_column: Vehicle pitch column in degrees.
    roll_column: Vehicle roll column in degrees.
    """

    latitude_column: str = "latitude"
    longitude_column: str = "longitude"
    heading_column: str = "heading"
    pitch_column: str = "pitch"
    roll_column: str = "roll"


@dataclass(slots=True, frozen=True)
class TransformCameraPosesCommand:
    """
    Command for transforming camera poses to vehicle reference-point poses.

    Attributes
    ----------
    input_file: Path to the camera pose CSV.
    output_file: Path to write the vehicle poses as CSV.
    """

    input_file: Path
    output_file: Path


@dataclass(slots=True, frozen=True)
class TransformCameraPosesBatchCommand:
    """
    Command for batch-transforming camera poses to vehicle reference-point poses.

    Attributes
    ----------
    input_dir: Directory containing camera pose CSV files.
    output_dir: Directory to write vehicle pose CSV files into.
    input_suffix: Suffix stripped from input filenames to derive the
        deployment label (e.g. ``"_renav_stereo_poses.csv"``).
    output_suffix: Suffix appended to the deployment label to form the
        output filename (e.g. ``"_vehicle_poses.csv"``).
    """

    input_dir: Path
    output_dir: Path
    input_suffix: str = "_renav_stereo_poses.csv"
    output_suffix: str = "_vehicle_poses.csv"


@dataclass(slots=True, frozen=True)
class TransformCameraPosesResult:
    """
    Result of transforming camera poses for a single deployment.

    Attributes
    ----------
    total: Number of vehicle poses written to the output file.
    """

    total: int


@dataclass(slots=True, frozen=True)
class TransformCameraPosesBatchResult:
    """
    Result of batch-transforming camera poses across deployments.

    Attributes
    ----------
    results: Per-deployment pose counts, keyed by deployment label.
    """

    results: dict[str, TransformCameraPosesResult]
