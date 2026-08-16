"""Generic geometric transforms over geodetic pose frames, as distinct from
`sensor_processors`, which holds sensor-family-specific processing."""

from collections.abc import Mapping
from typing import TypeVar

import geopandas as gpd
import numpy as np
import pandas as pd
import pymap3d
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from pydantic import BaseModel, ConfigDict, ValidationError

from afft.deployment import SensorExtrinsics

from .processor_registry import register_processor

Model = TypeVar("Model", bound=BaseModel)


class ApplyMountingOffsetConfig(BaseModel):
    """
    Column configuration for the apply mounting offset pipeline step.

    Attributes
    ----------
    heading_column: Heading column in degrees, clockwise from North.
    pitch_column: Pitch column in degrees.
    roll_column: Roll column in degrees.
    invert: Apply the extrinsics in the reverse direction (platform -> sensor
        rather than sensor -> platform).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

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
    outcome here: `apply_mounting_offset` has no uncorrected mode, so a
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


def apply_mounting_offset(
    poses: gpd.GeoDataFrame,
    extrinsics: SensorExtrinsics,
    config: ApplyMountingOffsetConfig,
) -> gpd.GeoDataFrame:
    """
    Apply a sensor's body-frame extrinsics to shift a geodetic pose frame by
    the full 3D lever arm.

    Reads longitude, latitude, height, and attitude from `poses`, offsets the
    position by the extrinsics translation rotated into the local NED frame
    by the pose's attitude, and writes the shifted position back to the
    geometry column. All other columns are passed through unchanged.

    Arguments
    ---------
    poses: Pose geoframe in the sensor's reference frame (or the body's
        reference frame, when `config.invert` is set). Position is a 3D
        `Point(longitude, latitude, height)`.
    extrinsics: The sensor's mounting pose in the body frame.
    config: Column configuration and transform direction.

    Returns
    -------
    Pose geoframe shifted to the body reference frame (or the reverse, when
    `config.invert` is set), with the same CRS as `poses`.
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

    source_longitude: NDArray[np.float64] = poses.geometry.x.to_numpy(
        dtype=np.float64
    )
    source_latitude: NDArray[np.float64] = poses.geometry.y.to_numpy(
        dtype=np.float64
    )
    source_height: NDArray[np.float64] = poses.geometry.z.to_numpy(
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

    result: gpd.GeoDataFrame = poses.copy()
    result["geometry"] = gpd.points_from_xy(
        target_longitude, target_latitude, target_up, crs=poses.crs
    )
    return result


@register_processor(
    "apply_mounting_offset", config_type=ApplyMountingOffsetConfig
)
def step_apply_mounting_offset(
    frames: Mapping[str, pd.DataFrame | gpd.GeoDataFrame],
    config: ApplyMountingOffsetConfig,
) -> gpd.GeoDataFrame:
    """Apply a sensor's body-frame extrinsics to shift a geodetic pose frame
    by the full 3D lever arm, in either direction."""
    extrinsics: SensorExtrinsics = _decode_single_row(
        frames["extrinsics"], SensorExtrinsics, "apply_mounting_offset"
    )
    return apply_mounting_offset(frames["poses"], extrinsics, config)
