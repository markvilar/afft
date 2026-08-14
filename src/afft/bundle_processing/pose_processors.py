"""Generic geometric transforms over geodetic pose frames, as distinct from
`sensor_processors`, which holds sensor-family-specific processing."""

from collections.abc import Mapping
from typing import TypeVar

import numpy as np
import pandas as pd
import pymap3d
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from pydantic import BaseModel, ConfigDict, ValidationError

from afft.deployment import SensorExtrinsics

from .processor_registry import register_processor

Model = TypeVar("Model", bound=BaseModel)


class ApplySensorExtrinsicsConfig(BaseModel):
    """
    Column configuration for the apply sensor extrinsics pipeline step.

    Attributes
    ----------
    latitude_column: Latitude column in the pose frame.
    longitude_column: Longitude column in the pose frame.
    height_column: Height column in the pose frame, in metres, positive up.
    heading_column: Heading column in degrees, clockwise from North.
    pitch_column: Pitch column in degrees.
    roll_column: Roll column in degrees.
    invert: Apply the extrinsics in the reverse direction (platform -> sensor
        rather than sensor -> platform).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    latitude_column: str = "latitude"
    longitude_column: str = "longitude"
    height_column: str = "height"
    heading_column: str = "heading"
    pitch_column: str = "pitch"
    roll_column: str = "roll"
    invert: bool = False


def _decode_single_row(
    frame: pd.DataFrame,
    model_type: type[Model],
    processor_key: str,
) -> Model:
    """
    Decode a one-row frame into `model_type`.

    Unlike `sensor_processors._decode_extrinsics`, absence is not a valid
    outcome here: `apply_sensor_extrinsics` has no uncorrected mode, so a
    missing or malformed extrinsics frame is always an error.

    Arguments
    ---------
    frame: The one-row frame to decode.
    model_type: The model the frame's single row must match.
    processor_key: Registered processor name, for the error messages.

    Returns
    -------
    The decoded model.

    Raises
    ------
    ValueError: If the frame does not hold exactly one row, or its columns do
        not match `model_type`.
    """
    if len(frame) != 1:
        raise ValueError(
            f"{processor_key}: frame holds {len(frame)} rows, expected"
            f" exactly 1"
        )

    expected: set[str] = set(model_type.model_fields)
    if set(frame.columns) != expected:
        raise ValueError(
            f"{processor_key}: frame does not match {model_type.__name__}:"
            f" columns are {sorted(frame.columns)}, expected"
            f" {sorted(expected)}"
        )

    try:
        return model_type(**frame.iloc[0].to_dict())
    except ValidationError as error:
        raise ValueError(
            f"{processor_key}: frame does not match {model_type.__name__}:"
            f" {error}"
        ) from error


def apply_sensor_extrinsics(
    poses: pd.DataFrame,
    extrinsics: SensorExtrinsics,
    config: ApplySensorExtrinsicsConfig,
) -> pd.DataFrame:
    """
    Apply a sensor's body-frame extrinsics to shift a geodetic pose frame by
    the full 3D lever arm.

    Reads latitude, longitude, height, and attitude from `poses`, offsets the
    position by the extrinsics translation rotated into the local NED frame
    by the pose's attitude, and writes the shifted latitude, longitude, and
    height back. All other columns are passed through unchanged.

    Arguments
    ---------
    poses: Pose frame in the sensor's reference frame (or the body's
        reference frame, when `config.invert` is set).
    extrinsics: The sensor's mounting pose in the body frame.
    config: Column configuration and transform direction.

    Returns
    -------
    Pose frame shifted to the body reference frame (or the reverse, when
    `config.invert` is set).
    """
    headings: NDArray[np.float64] = poses[config.heading_column].to_numpy(
        dtype=np.float64
    )
    pitches: NDArray[np.float64] = poses[config.pitch_column].to_numpy(
        dtype=np.float64
    )
    rolls: NDArray[np.float64] = poses[config.roll_column].to_numpy(
        dtype=np.float64
    )

    rotation: Rotation = Rotation.from_euler(
        "ZYX",
        np.column_stack([headings, pitches, rolls]),
        degrees=True,
    )

    # Extrinsics translation is in the body frame (SNAME: x=forward,
    # y=starboard, z=down), which is aligned with NED, so no sign conversion
    # is needed beyond the translation direction itself.
    sensor_in_body: NDArray[np.float64] = np.array(
        [extrinsics.locx, extrinsics.locy, extrinsics.locz],
        dtype=np.float64,
    )
    offset: NDArray[np.float64] = (
        sensor_in_body if config.invert else -sensor_in_body
    )
    delta_ned: NDArray[np.float64] = rotation.apply(offset)

    source_latitude: NDArray[np.float64] = poses[
        config.latitude_column
    ].to_numpy(dtype=np.float64)
    source_longitude: NDArray[np.float64] = poses[
        config.longitude_column
    ].to_numpy(dtype=np.float64)
    source_height: NDArray[np.float64] = poses[config.height_column].to_numpy(
        dtype=np.float64
    )

    target_latitude: NDArray[np.float64]
    target_longitude: NDArray[np.float64]
    target_up: NDArray[np.float64]
    target_latitude, target_longitude, target_up = pymap3d.ned2geodetic(
        delta_ned[:, 0],
        delta_ned[:, 1],
        delta_ned[:, 2],
        source_latitude,
        source_longitude,
        source_height,
    )

    shifted: pd.DataFrame = poses.copy()
    shifted[config.latitude_column] = target_latitude
    shifted[config.longitude_column] = target_longitude
    shifted[config.height_column] = target_up
    return shifted


@register_processor(
    "apply_sensor_extrinsics", config_type=ApplySensorExtrinsicsConfig
)
def step_apply_sensor_extrinsics(
    frames: Mapping[str, pd.DataFrame],
    config: ApplySensorExtrinsicsConfig,
) -> pd.DataFrame:
    """Apply a sensor's body-frame extrinsics to shift a geodetic pose frame
    by the full 3D lever arm, in either direction."""
    extrinsics: SensorExtrinsics = _decode_single_row(
        frames["extrinsics"], SensorExtrinsics, "apply_sensor_extrinsics"
    )
    return apply_sensor_extrinsics(frames["poses"], extrinsics, config)
