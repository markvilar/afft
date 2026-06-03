"""Position resolution, uncertainty, and orchestration for TrackLink USBL."""

import numpy as np
import pandas as pd
import pymap3d
from scipy.spatial.transform import Rotation

from numpy.typing import NDArray

from .types import (
    UsblProcessingConfig,
    UsblResolvePositionConfig,
    UsblTransceiverExtrinsics,
    UsblUncertaintyConfig,
)

_NS_PER_S: float = 1e9
_ZERO_EXTRINSICS: UsblTransceiverExtrinsics = UsblTransceiverExtrinsics(
    x=0.0, y=0.0, z=0.0
)


def resolve_usbl_position(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblResolvePositionConfig = UsblResolvePositionConfig(),
) -> pd.DataFrame:
    """Resolve AUV lat/lon from TrackLink USBL bearing, slant range, and depth.

    Depth from the pressure DataFrame is interpolated to USBL timestamps.
    The raw bearing is treated as an azimuth in the transceiver body frame
    (0 = transceiver forward, clockwise). The ZYX attitude chain is applied:
    transceiver → ship body (via extrinsics rotation) → NED (via ship attitude).
    When config.extrinsics is None a zero-offset, zero-rotation transceiver is
    used, so bearing is relative to the ship bow and heading is applied via the
    rotation chain.

    The transceiver geodetic position is computed by rotating the body-frame
    translation through the ship attitude and calling pymap3d.ned2geodetic.
    The corrected direction vector × slant range gives the target NED offset
    from the transceiver, which is converted to geodetic via ned2geodetic.

    Adds columns: target_depth, target_x, target_y, target_z,
                  target_horizontal_range, target_inclination_angle,
                  target_latitude, target_longitude.
    """
    _validate_time_alignment(usbl, pressure, config)

    result: pd.DataFrame = usbl.copy()
    result["target_depth"] = _interpolate_depth(usbl, pressure, config)

    extrinsics: UsblTransceiverExtrinsics = (
        config.extrinsics if config.extrinsics is not None else _ZERO_EXTRINSICS
    )

    ship_attitudes_ypr: NDArray[np.float64] = np.column_stack(
        [
            result[config.ship_heading_col].to_numpy(),
            result[config.ship_pitch_col].to_numpy(),
            result[config.ship_roll_col].to_numpy(),
        ]
    )

    ship_locations_geo: NDArray[np.float64] = np.column_stack(
        [
            result[config.ship_lat_col].to_numpy(),
            result[config.ship_lon_col].to_numpy(),
            np.zeros_like(result[config.ship_lat_col].to_numpy()),
        ]
    )

    # Per-row ship body → NED rotation (ZYX intrinsic: heading, pitch, roll).
    R_ship: Rotation = Rotation.from_euler(
        "zyx", ship_attitudes_ypr, degrees=True
    )

    # Step 1 - Transceiver NED offset from the ship GPS antenna.
    transceiver_ned: NDArray[np.float64] = R_ship.apply(
        np.tile(extrinsics.translation, (len(result), 1))
    )

    # Step 2 - Target position in transceiver sensor frame: bearing + slant range + depth
    # relative to the transceiver origin.
    depth: NDArray[np.float64] = result["target_depth"].to_numpy()
    slant_range: NDArray[np.float64] = result[config.range_col].to_numpy()
    depth_relative: NDArray[np.float64] = depth - transceiver_ned[:, 2]
    target_xyz_sensor: NDArray[np.float64] = (
        _calculate_target_xyz_from_range_bearing(
            slant_range=slant_range,
            bearing_deg=result[config.bearing_col].to_numpy(),
            depth=depth_relative,
        )
    )
    # Step 3 - Rotate target from transceiver frame → ship body → NED, then convert the
    # transceiver and target positions to geodetic (WGS84).
    target_ned: NDArray[np.float64] = R_ship.apply(
        extrinsics.rotation.apply(target_xyz_sensor)
    )

    # Step 4 - Calculate target XYZ in vessel frame
    target_xyz_vessel: NDArray[np.float64] = extrinsics.transform.apply(
        target_xyz_sensor
    )

    # Calculate horizontal range and inclination angle to target
    target_horizontal_range: NDArray[np.float64] = np.sqrt(
        target_xyz_vessel[:, 0] ** 2 + target_xyz_vessel[:, 1] ** 2
    )
    target_inclination_angle: NDArray[np.float64] = np.degrees(
        np.arcsin(np.clip(depth_relative / slant_range, -1.0, 1.0))
    )

    transceiver_lat: NDArray[np.float64]
    transceiver_lon: NDArray[np.float64]
    transceiver_alt: NDArray[np.float64]
    transceiver_lat, transceiver_lon, transceiver_alt = pymap3d.ned2geodetic(
        transceiver_ned[:, 0],
        transceiver_ned[:, 1],
        transceiver_ned[:, 2],
        ship_locations_geo[:, 0],
        ship_locations_geo[:, 1],
        ship_locations_geo[:, 2],
    )

    target_latitude: NDArray[np.float64]
    target_longitude: NDArray[np.float64]
    target_latitude, target_longitude, _ = pymap3d.ned2geodetic(
        target_ned[:, 0],
        target_ned[:, 1],
        target_ned[:, 2],
        transceiver_lat,
        transceiver_lon,
        transceiver_alt,
    )

    result["target_x"] = target_xyz_vessel[:, 0]
    result["target_y"] = target_xyz_vessel[:, 1]
    result["target_z"] = target_xyz_vessel[:, 2]
    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["target_latitude"] = target_latitude
    result["target_longitude"] = target_longitude

    return result


def estimate_usbl_uncertainty(
    df: pd.DataFrame,
    config: UsblUncertaintyConfig = UsblUncertaintyConfig(),
) -> pd.DataFrame:
    """Add horizontal_position_std and depth_position_std columns to a resolved USBL table.

    Values are deployment-calibrated scalars read directly from config rather
    than derived from a quadrature formula.

    Arguments
    ---------
    df: Resolved USBL DataFrame.
    config: Deployment-calibrated uncertainty values.

    Returns
    -------
    DataFrame with horizontal_position_std and depth_position_std columns added.
    """
    result: pd.DataFrame = df.copy()
    result["horizontal_position_std"] = config.horizontal_position_std
    result["depth_position_std"] = config.depth_position_std
    return result


def process_tracklink_usbl(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblProcessingConfig = UsblProcessingConfig(),
) -> pd.DataFrame:
    """Resolve positions and estimate uncertainty from TrackLink USBL data.

    Arguments
    ---------
    usbl: TrackLink USBL observations with bearing, range, and ship position.
    pressure: Pressure sensor depth readings to interpolate at USBL timestamps.
    config: Combined configuration for position resolution and uncertainty estimation.

    Returns
    -------
    DataFrame with resolved target positions and uncertainty columns.
    """
    result: pd.DataFrame = resolve_usbl_position(usbl, pressure, config.resolve)
    result = estimate_usbl_uncertainty(result, config.uncertainty)
    return result


def _validate_time_alignment(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblResolvePositionConfig,
) -> None:
    """Raise ValueError if USBL pings fall outside the pressure time window.

    Arguments
    ---------
    usbl: USBL DataFrame with a timestamp column.
    pressure: Pressure sensor DataFrame with a timestamp column.
    config: Position resolution config supplying column names and the gap limit.
    """
    usbl_time: NDArray[np.float64] = (
        pd.to_datetime(usbl[config.timestamp_col], format="ISO8601")
        .astype(np.int64)
        .to_numpy()
    )
    pressure_time: NDArray[np.float64] = (
        pd.to_datetime(pressure[config.timestamp_col], format="ISO8601")
        .astype(np.int64)
        .to_numpy()
    )
    early_gap_s: float = (
        max(0.0, float(pressure_time.min() - usbl_time.min())) / _NS_PER_S
    )
    late_gap_s: float = (
        max(0.0, float(usbl_time.max() - pressure_time.max())) / _NS_PER_S
    )
    if early_gap_s > config.max_time_gap_seconds:
        raise ValueError(
            f"First USBL ping precedes first pressure reading by "
            f"{early_gap_s:.1f} s (limit: {config.max_time_gap_seconds} s)"
        )
    if late_gap_s > config.max_time_gap_seconds:
        raise ValueError(
            f"Last USBL ping follows last pressure reading by "
            f"{late_gap_s:.1f} s (limit: {config.max_time_gap_seconds} s)"
        )


def _interpolate_depth(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblResolvePositionConfig,
) -> NDArray[np.float64]:
    """Interpolate pressure sensor depth to USBL ping timestamps.

    Arguments
    ---------
    usbl: USBL DataFrame with a timestamp column.
    pressure: Pressure sensor DataFrame with timestamp and depth columns.
    config: Position resolution config supplying column names.

    Returns
    -------
    Depth values interpolated at each USBL ping timestamp.
    """
    usbl_time: NDArray[np.float64] = (
        pd.to_datetime(usbl[config.timestamp_col], format="ISO8601")
        .astype(np.int64)
        .to_numpy()
    )
    pressure_time_series: pd.Series[int] = pd.to_datetime(
        pressure[config.timestamp_col], format="ISO8601"
    ).sort_values()
    pressure_time: NDArray[np.float64] = pressure_time_series.astype(
        np.int64
    ).to_numpy()
    pressure_depth: NDArray[np.float64] = pressure.loc[
        pressure_time_series.index, config.depth_col
    ].to_numpy()
    return np.interp(usbl_time, pressure_time, pressure_depth)


def _calculate_target_xyz_from_range_bearing(
    slant_range: NDArray[np.float64],
    bearing_deg: NDArray[np.float64],
    depth: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute target position in sensor frame from slant range, bearing, and depth.

    Converts spherical USBL observations to a Cartesian (x, y, z) position in
    the transceiver sensor frame. No extrinsics or attitude compensation applied.

    Arguments
    ---------
    slant_range: Slant range from transceiver to target (m).
    bearing_deg: Bearing from transceiver to target (degrees).
    depth: Interpolated target depth (m, positive downward).

    Returns
    -------
    Array of shape (N, 3) with columns [x, y, z] in the sensor frame.
    """
    bearing_rad: NDArray[np.float64] = np.radians(bearing_deg)
    horizontal_range: NDArray[np.float64] = np.sqrt(
        np.maximum(slant_range**2 - depth**2, 0.0)
    )
    return np.column_stack(
        [
            horizontal_range * np.cos(bearing_rad),
            horizontal_range * np.sin(bearing_rad),
            depth,
        ]
    )
