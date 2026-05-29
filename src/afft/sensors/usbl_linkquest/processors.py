"""Position resolution, uncertainty, and orchestration for TrackLink USBL."""

import numpy as np
import pandas as pd
import pymap3d
from scipy.spatial.transform import Rotation

from numpy.typing import NDArray

from afft.telemetry_processing.pipeline import register_processor

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


@register_processor("resolve_usbl_position")
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

    Adds columns: target_depth, horizontal_range,
                  target_latitude, target_longitude.
    """
    _validate_time_alignment(usbl, pressure, config)

    result: pd.DataFrame = usbl.copy()
    result["target_depth"] = _interpolate_depth(usbl, pressure, config)

    extrinsics: UsblTransceiverExtrinsics = (
        config.extrinsics if config.extrinsics is not None else _ZERO_EXTRINSICS
    )

    depth: NDArray[np.float64] = result["target_depth"].to_numpy()
    slant_range: NDArray[np.float64] = result[config.range_col].to_numpy()
    ship_lat: NDArray[np.float64] = result[config.ship_lat_col].to_numpy()
    ship_lon: NDArray[np.float64] = result[config.ship_lon_col].to_numpy()
    n_rows: int = len(depth)

    ship_heading: NDArray[np.float64] = result[
        config.ship_heading_col
    ].to_numpy()
    ship_pitch: NDArray[np.float64] = result[config.ship_pitch_col].to_numpy()
    ship_roll: NDArray[np.float64] = result[config.ship_roll_col].to_numpy()

    # Per-row ship body → NED rotation (ZYX intrinsic: heading, pitch, roll).
    R_ship: Rotation = Rotation.from_euler(
        "zyx",
        np.column_stack([ship_heading, ship_pitch, ship_roll]),
        degrees=True,
    )

    # Transceiver NED offset from ship GPS, then geodetic position.
    trans_body: NDArray[np.float64] = np.array(
        [extrinsics.x, extrinsics.y, extrinsics.z], dtype=np.float64
    )
    trans_ned: NDArray[np.float64] = R_ship.apply(
        np.tile(trans_body, (n_rows, 1))
    )
    trans_lat: NDArray[np.float64]
    trans_lon: NDArray[np.float64]
    trans_alt: NDArray[np.float64]
    trans_lat, trans_lon, trans_alt = pymap3d.ned2geodetic(
        trans_ned[:, 0],
        trans_ned[:, 1],
        trans_ned[:, 2],
        ship_lat,
        ship_lon,
        np.zeros_like(ship_lat),
    )

    # AUV depth relative to transceiver and resulting horizontal range.
    depth_rel: NDArray[np.float64] = depth - trans_ned[:, 2]
    horizontal_range: NDArray[np.float64] = np.sqrt(
        np.maximum(slant_range**2 - depth_rel**2, 0.0)
    )

    # Direction unit vector in transceiver frame from bearing and depth.
    bearing_t_rad: NDArray[np.float64] = np.radians(
        result[config.bearing_col].to_numpy()
    )
    el_t: NDArray[np.float64] = -np.arcsin(
        np.minimum(depth_rel / slant_range, 1.0)
    )
    cos_el_t: NDArray[np.float64] = np.cos(el_t)
    dirs_transceiver: NDArray[np.float64] = np.column_stack(
        [
            cos_el_t * np.cos(bearing_t_rad),
            cos_el_t * np.sin(bearing_t_rad),
            -np.sin(el_t),
        ]
    )

    # Rotate transceiver frame → ship body (constant) → NED (per-row).
    R_ext: Rotation = Rotation.from_euler(
        "zyx", [extrinsics.psi, extrinsics.theta, extrinsics.phi], degrees=False
    )
    dirs_ned: NDArray[np.float64] = R_ship.apply(R_ext.apply(dirs_transceiver))

    # Target geodetic position: transceiver origin + NED offset.
    target_ned: NDArray[np.float64] = dirs_ned * slant_range[:, np.newaxis]
    target_latitude: NDArray[np.float64]
    target_longitude: NDArray[np.float64]
    target_latitude, target_longitude, _ = pymap3d.ned2geodetic(
        target_ned[:, 0],
        target_ned[:, 1],
        target_ned[:, 2],
        trans_lat,
        trans_lon,
        trans_alt,
    )

    result["horizontal_range"] = horizontal_range
    result["target_latitude"] = target_latitude
    result["target_longitude"] = target_longitude

    return result


@register_processor("estimate_usbl_uncertainty")
def estimate_usbl_uncertainty(
    df: pd.DataFrame,
    config: UsblUncertaintyConfig = UsblUncertaintyConfig(),
) -> pd.DataFrame:
    """Add a position_uncertainty column to a resolved USBL table.

    Propagates two independent error sources through the slant-range geometry:

        σ_pos = sqrt((σ_R · R / h)² + (h · σ_θ)²)

    where R is slant range, h is horizontal range, σ_R is range_uncertainty
    in metres, and σ_θ is bearing_uncertainty converted to radians.

    horizontal_range must already be present (produced by resolve_usbl_position).
    When horizontal_range is near zero the range term is clamped to avoid
    division by zero; the AUV is directly below the ship and position
    uncertainty collapses to the range measurement error.
    """
    if config.horizontal_range_col not in df.columns:
        raise KeyError(
            f"{config.horizontal_range_col!r} not found — "
            "run resolve_usbl_position before estimate_usbl_uncertainty"
        )

    result: pd.DataFrame = df.copy()

    slant_range: NDArray[np.float64] = result[config.range_col].to_numpy()
    horizontal_range: NDArray[np.float64] = result[
        config.horizontal_range_col
    ].to_numpy()
    bearing_uncertainty_rad: float = np.radians(config.bearing_uncertainty)

    h_safe: NDArray[np.float64] = np.maximum(
        horizontal_range, config.min_horizontal_range
    )
    range_term: NDArray[np.float64] = (
        config.range_uncertainty * slant_range / h_safe
    )
    bearing_term: NDArray[np.float64] = (
        horizontal_range * bearing_uncertainty_rad
    )

    result["position_uncertainty"] = np.sqrt(range_term**2 + bearing_term**2)

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
    DataFrame with resolved target positions and position uncertainty column.
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
