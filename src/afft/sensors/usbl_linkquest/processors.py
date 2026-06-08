"""Position resolution, uncertainty, and orchestration for the LinkQuest TrackLink 1500HA USBL."""

import numpy as np
import pandas as pd
import pymap3d
from scipy.spatial.transform import Rotation

from numpy.typing import NDArray

from afft.utils.log import logger

from .types import (
    TrackLinkProcessingFromLogsConfig,
    TrackLinkProcessingFromMessagesConfig,
    TrackLinkResolvePositionFromLogsConfig,
    TrackLinkResolvePositionFromMessagesConfig,
    TrackLinkTransceiverExtrinsics,
    TrackLinkUncertaintyConfig,
)

_NS_PER_S: float = 1e9


def resolve_target_position_from_messages(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: TrackLinkResolvePositionFromMessagesConfig = TrackLinkResolvePositionFromMessagesConfig(),
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

    Adds columns: target_depth, target_x_sensor, target_y_sensor, target_z_sensor,
                  target_x_vessel, target_y_vessel, target_z_vessel,
                  target_horizontal_range, target_inclination_angle,
                  target_latitude, target_longitude, target_height,
                  usbl_extrinsics_locx, usbl_extrinsics_locy, usbl_extrinsics_locz,
                  usbl_extrinsics_rotx, usbl_extrinsics_roty, usbl_extrinsics_rotz.
    """
    _validate_time_alignment(usbl, pressure, config)

    result: pd.DataFrame = usbl.copy()
    result["target_depth"] = _interpolate_depth(usbl, pressure, config)

    extrinsics: TrackLinkTransceiverExtrinsics = (
        config.extrinsics
        if config.extrinsics is not None
        else TrackLinkTransceiverExtrinsics()
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
    target_xyz_usbl: NDArray[np.float64] = _solve_target_xyz_sensor_frame(
        slant_range=slant_range,
        bearing_deg=result[config.bearing_col].to_numpy(),
        depth=depth_relative,
        ship_rotation=R_ship,
        extrinsics_rotation=extrinsics.rotation,
    )
    # Step 3 - Rotate target from transceiver frame → ship body → NED, then convert the
    # transceiver and target positions to geodetic (WGS84).
    target_ned: NDArray[np.float64] = R_ship.apply(
        extrinsics.rotation.apply(target_xyz_usbl)
    )

    # Step 4 - Calculate target XYZ in vessel frame
    target_xyz_vessel: NDArray[np.float64] = extrinsics.transform.apply(
        target_xyz_usbl
    )

    # Calculate horizontal range and inclination angle to target
    target_horizontal_range: NDArray[np.float64] = np.sqrt(
        target_xyz_vessel[:, 0] ** 2 + target_xyz_vessel[:, 1] ** 2
    )
    target_inclination_angle: NDArray[np.float64] = np.degrees(
        np.arcsin(np.clip(target_xyz_usbl[:, 2] / slant_range, -1.0, 1.0))
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
    target_height: NDArray[np.float64]
    target_latitude, target_longitude, target_height = pymap3d.ned2geodetic(
        target_ned[:, 0],
        target_ned[:, 1],
        target_ned[:, 2],
        transceiver_lat,
        transceiver_lon,
        transceiver_alt,
    )

    result["target_x_sensor"] = target_xyz_usbl[:, 0]
    result["target_y_sensor"] = target_xyz_usbl[:, 1]
    result["target_z_sensor"] = target_xyz_usbl[:, 2]
    result["target_x_vessel"] = target_xyz_vessel[:, 0]
    result["target_y_vessel"] = target_xyz_vessel[:, 1]
    result["target_z_vessel"] = target_xyz_vessel[:, 2]
    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["target_latitude"] = target_latitude
    result["target_longitude"] = target_longitude
    result["target_height"] = target_height
    result["usbl_extrinsics_locx"] = extrinsics.locx
    result["usbl_extrinsics_locy"] = extrinsics.locy
    result["usbl_extrinsics_locz"] = extrinsics.locz
    result["usbl_extrinsics_rotx"] = extrinsics.rotx
    result["usbl_extrinsics_roty"] = extrinsics.roty
    result["usbl_extrinsics_rotz"] = extrinsics.rotz

    return result


def estimate_usbl_uncertainty(
    df: pd.DataFrame,
    config: TrackLinkUncertaintyConfig = TrackLinkUncertaintyConfig(),
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


def process_tracklink_usbl_from_messages(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: TrackLinkProcessingFromMessagesConfig = TrackLinkProcessingFromMessagesConfig(),
) -> pd.DataFrame:
    """Resolve positions and estimate uncertainty from TrackLink AUV messages.

    Arguments
    ---------
    usbl: TrackLink USBL observations with bearing, range, and ship position.
    pressure: Pressure sensor depth readings to interpolate at USBL timestamps.
    config: Combined configuration for position resolution and uncertainty estimation.

    Returns
    -------
    DataFrame with resolved target positions and uncertainty columns.
    """
    result: pd.DataFrame = resolve_target_position_from_messages(
        usbl, pressure, config.resolve
    )
    result = estimate_usbl_uncertainty(result, config.uncertainty)
    return result


def resolve_target_position_from_logs(
    usbl: pd.DataFrame,
    config: TrackLinkResolvePositionFromLogsConfig = TrackLinkResolvePositionFromLogsConfig(),
) -> pd.DataFrame:
    """Resolve AUV lat/lon from TrackLink USBL log entries with target XYZ.

    Target XYZ in the sensor frame is taken directly from the log DataFrame.
    The ZYX attitude chain is applied: transceiver → ship body (via extrinsics
    rotation) → NED (via ship attitude). When config.extrinsics is None a
    zero-offset, zero-rotation transceiver is assumed.

    The transceiver geodetic position is computed by rotating the body-frame
    translation through the ship attitude and calling pymap3d.ned2geodetic.
    The target NED offset from the transceiver is converted to geodetic via
    ned2geodetic.

    Adds columns: target_depth, target_x_sensor, target_y_sensor, target_z_sensor,
                  target_x_vessel, target_y_vessel, target_z_vessel,
                  target_horizontal_range, target_inclination_angle,
                  target_latitude, target_longitude, target_height,
                  usbl_extrinsics_locx, usbl_extrinsics_locy, usbl_extrinsics_locz,
                  usbl_extrinsics_rotx, usbl_extrinsics_roty, usbl_extrinsics_rotz.
    """
    _validate_logs_contain_target_xyz(usbl, config)

    result: pd.DataFrame = usbl.copy()

    extrinsics: TrackLinkTransceiverExtrinsics = (
        config.extrinsics
        if config.extrinsics is not None
        else TrackLinkTransceiverExtrinsics()
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

    R_ship: Rotation = Rotation.from_euler(
        "zyx", ship_attitudes_ypr, degrees=True
    )

    # Step 1 - Transceiver NED offset from the ship GPS antenna.
    transceiver_ned: NDArray[np.float64] = R_ship.apply(
        np.tile(extrinsics.translation, (len(result), 1))
    )

    # Step 2 - Target position in sensor frame, taken directly from log entries.
    target_xyz_sensor: NDArray[np.float64] = np.column_stack(
        [
            result[config.target_x_col].to_numpy(),
            result[config.target_y_col].to_numpy(),
            result[config.target_z_col].to_numpy(),
        ]
    )

    # Step 3 - Rotate target from transceiver frame → ship body → NED.
    target_ned: NDArray[np.float64] = R_ship.apply(
        extrinsics.rotation.apply(target_xyz_sensor)
    )

    # Step 4 - Calculate target XYZ in vessel frame.
    target_xyz_vessel: NDArray[np.float64] = extrinsics.transform.apply(
        target_xyz_sensor
    )

    target_depth: NDArray[np.float64] = transceiver_ned[:, 2] + target_ned[:, 2]
    target_horizontal_range: NDArray[np.float64] = np.sqrt(
        target_xyz_vessel[:, 0] ** 2 + target_xyz_vessel[:, 1] ** 2
    )
    slant_range: NDArray[np.float64] = result[config.range_col].to_numpy()
    target_inclination_angle: NDArray[np.float64] = np.degrees(
        np.arcsin(np.clip(target_xyz_sensor[:, 2] / slant_range, -1.0, 1.0))
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
    target_height: NDArray[np.float64]
    target_latitude, target_longitude, target_height = pymap3d.ned2geodetic(
        target_ned[:, 0],
        target_ned[:, 1],
        target_ned[:, 2],
        transceiver_lat,
        transceiver_lon,
        transceiver_alt,
    )

    result["target_depth"] = target_depth
    result["target_x_sensor"] = target_xyz_sensor[:, 0]
    result["target_y_sensor"] = target_xyz_sensor[:, 1]
    result["target_z_sensor"] = target_xyz_sensor[:, 2]
    result["target_x_vessel"] = target_xyz_vessel[:, 0]
    result["target_y_vessel"] = target_xyz_vessel[:, 1]
    result["target_z_vessel"] = target_xyz_vessel[:, 2]
    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["target_latitude"] = target_latitude
    result["target_longitude"] = target_longitude
    result["target_height"] = target_height
    result["usbl_extrinsics_locx"] = extrinsics.locx
    result["usbl_extrinsics_locy"] = extrinsics.locy
    result["usbl_extrinsics_locz"] = extrinsics.locz
    result["usbl_extrinsics_rotx"] = extrinsics.rotx
    result["usbl_extrinsics_roty"] = extrinsics.roty
    result["usbl_extrinsics_rotz"] = extrinsics.rotz

    return result


def process_tracklink_usbl_from_logs(
    usbl: pd.DataFrame,
    config: TrackLinkProcessingFromLogsConfig = TrackLinkProcessingFromLogsConfig(),
) -> pd.DataFrame:
    """Resolve positions and estimate uncertainty from TrackLink USBL log entries.

    Arguments
    ---------
    usbl: Merged TrackLink log DataFrame with ship position, ship attitude,
        and target XYZ in sensor frame.
    config: Combined configuration for position resolution and uncertainty estimation.

    Returns
    -------
    DataFrame with resolved target positions and uncertainty columns.
    """
    result: pd.DataFrame = resolve_target_position_from_logs(
        usbl, config.resolve
    )
    result = estimate_usbl_uncertainty(result, config.uncertainty)
    return result


def _validate_logs_contain_target_xyz(
    usbl: pd.DataFrame,
    config: TrackLinkResolvePositionFromLogsConfig,
) -> None:
    """Raise ValueError if target XYZ columns are missing or entirely NaN.

    Arguments
    ---------
    usbl: USBL DataFrame to validate.
    config: Position resolution config supplying target XYZ column names.
    """
    xyz_cols: list[str] = [
        config.target_x_col,
        config.target_y_col,
        config.target_z_col,
    ]
    missing: list[str] = [col for col in xyz_cols if col not in usbl.columns]
    if missing:
        logger.warning(f"Target XYZ columns missing from DataFrame: {missing}")
        raise ValueError(
            f"Target XYZ columns missing from DataFrame: {missing}"
        )
    all_nan: list[str] = [col for col in xyz_cols if usbl[col].isna().all()]
    if all_nan:
        logger.warning(f"Target XYZ columns are all NaN: {all_nan}")
        raise ValueError(f"Target XYZ columns are all NaN: {all_nan}")


def _validate_time_alignment(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: TrackLinkResolvePositionFromMessagesConfig,
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
    config: TrackLinkResolvePositionFromMessagesConfig,
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


def _solve_target_xyz_sensor_frame(
    slant_range: NDArray[np.float64],
    bearing_deg: NDArray[np.float64],
    depth: NDArray[np.float64],
    ship_rotation: Rotation,
    extrinsics_rotation: Rotation,
) -> NDArray[np.float64]:
    """Compute target position in sensor frame from slant range, bearing, and depth.

    Solves for the sensor-frame Cartesian position consistent with the measured
    slant range, a bearing defined in the sensor horizontal plane, and the known
    world-frame (NED) depth of the target. Accounts for the full rotation chain
    R_total = R_ship @ R_extrinsics, so the result is correct even when the
    transceiver is mounted at a roll or pitch angle.

    Assumption: bearing is measured in the sensor horizontal plane (perpendicular
    to the sensor Z-axis), not as a compass-referenced azimuth.

    Steps:
    1. Extract the world-down direction in sensor coordinates from the third row
       of R_total = R_ship @ R_extrinsics.
    2. Project that row onto the bearing direction (bearing_projection, A) and
       the sensor Z-axis (z_projection, B), giving depth = A·r_h + B·z_s.
    3. Combine with the slant-range constraint r_h² + z_s² = r² to form a
       quadratic in r_h; select the non-negative root.
    4. Recover z_s from the depth constraint: z_s = (d − A·r_h) / B.
    5. Return [r_h·cos(b), r_h·sin(b), z_s].

    See issue #110 for the full derivation.

    Arguments
    ---------
    slant_range: Slant range from transceiver to target (m).
    bearing_deg: Bearing in the sensor horizontal plane (degrees, 0 = sensor
        X-axis, clockwise).
    depth: Target depth relative to the transceiver origin in the world NED
        frame (m, positive downward).
    ship_rotation: Per-row batch rotation from ship body frame to NED frame.
    extrinsics_rotation: Single rotation from sensor frame to ship body frame.

    Returns
    -------
    Array of shape (N, 3) with columns [x_s, y_s, z_s] in the sensor frame.
    """
    # Step 1 — Extract the world-depth (NED Z) direction in sensor coordinates.
    # The third row of R_total = R_ship @ R_extrinsics is a unit vector whose
    # dot product with any sensor-frame vector gives the world-down component.
    depth_row: NDArray[np.float64] = (
        ship_rotation * extrinsics_rotation
    ).as_matrix()[:, 2, :]  # (N, 3)

    # Step 2 — Project the depth row onto the bearing direction and sensor Z-axis.
    # bearing_projection (A) and z_projection (B) satisfy:
    #   depth = A * horizontal_range + B * sensor_z
    bearing_rad: NDArray[np.float64] = np.radians(bearing_deg)
    cos_bearing: NDArray[np.float64] = np.cos(bearing_rad)
    sin_bearing: NDArray[np.float64] = np.sin(bearing_rad)

    bearing_projection: NDArray[np.float64] = (
        depth_row[:, 0] * cos_bearing + depth_row[:, 1] * sin_bearing
    )
    z_projection: NDArray[np.float64] = depth_row[:, 2]

    # Step 3 — Solve the quadratic in horizontal_range (positive root).
    # Substituting sensor_z = (depth - A * r_h) / B into r_h² + sensor_z² = r²
    # yields: (A² + B²) * r_h² - 2*A*d*r_h + (d² - r²*B²) = 0
    # Discriminant = 4*B²*(r²*(A²+B²) - d²)
    discriminant_inner: NDArray[np.float64] = (
        slant_range**2 * (bearing_projection**2 + z_projection**2) - depth**2
    )
    horizontal_range: NDArray[np.float64] = np.maximum(
        (
            bearing_projection * depth
            + np.abs(z_projection)
            * np.sqrt(np.maximum(discriminant_inner, 0.0))
        )
        / np.maximum(bearing_projection**2 + z_projection**2, 1e-18),
        0.0,
    )

    # Step 4 — Recover the sensor-frame Z component from the depth constraint.
    safe_z_projection: NDArray[np.float64] = np.where(
        np.abs(z_projection) > 1e-9,
        z_projection,
        np.copysign(1e-9, z_projection),
    )
    sensor_z: NDArray[np.float64] = (
        depth - bearing_projection * horizontal_range
    ) / safe_z_projection

    return np.column_stack(
        [
            horizontal_range * cos_bearing,
            horizontal_range * sin_bearing,
            sensor_z,
        ]
    )
