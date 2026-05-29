"""Position resolution, uncertainty, and orchestration for TrackLink USBL."""

import numpy as np
import pandas as pd
import pymap3d

from numpy.typing import NDArray

from afft.telemetry_processing.pipeline import register_processor

from .types import (
    UsblProcessingConfig,
    UsblResolvePositionConfig,
    UsblUncertaintyConfig,
)

_NS_PER_S: float = 1e9


@register_processor("resolve_usbl_position")
def resolve_usbl_position(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblResolvePositionConfig = UsblResolvePositionConfig(),
) -> pd.DataFrame:
    """Resolve AUV lat/lon from TrackLink USBL bearing, slant range, and depth.

    Depth from the pressure DataFrame is interpolated to USBL timestamps.
    Horizontal range is computed as sqrt(slant_range² - depth²).
    The AUV position is projected from the ship position using
    pymap3d.aer2geodetic on the WGS84 ellipsoid.

    bearing_reference: "absolute" treats bearing as a compass bearing;
    "relative" adds ship heading to obtain the compass bearing first.

    Adds columns: target_depth, horizontal_range,
                  target_latitude, target_longitude.
    """
    _validate_time_alignment(usbl, pressure, config)

    result: pd.DataFrame = usbl.copy()

    result["target_depth"] = _interpolate_depth(usbl, pressure, config)

    if config.bearing_reference == "relative":
        bearing: pd.Series = (
            result[config.bearing_col] + result[config.ship_heading_col]
        ) % 360.0
    else:
        bearing = result[config.bearing_col]

    depth: NDArray[np.float64] = result["target_depth"].to_numpy()
    slant_range: NDArray[np.float64] = result[config.range_col].to_numpy()
    horizontal_range: NDArray[np.float64] = np.sqrt(
        np.maximum(slant_range**2 - depth**2, 0.0)
    )

    elevation: NDArray[np.float64] = -np.degrees(
        np.arcsin(np.minimum(depth / slant_range, 1.0))
    )

    ship_lat: NDArray[np.float64] = result[config.ship_lat_col].to_numpy()
    ship_lon: NDArray[np.float64] = result[config.ship_lon_col].to_numpy()

    target_latitude, target_longitude, _ = pymap3d.aer2geodetic(
        bearing.to_numpy(),
        elevation,
        slant_range,
        ship_lat,
        ship_lon,
        np.zeros_like(ship_lat),
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
    pressure_time_series: pd.Series = pd.to_datetime(
        pressure[config.timestamp_col], format="ISO8601"
    ).sort_values()
    pressure_time: NDArray[np.float64] = pressure_time_series.astype(
        np.int64
    ).to_numpy()
    pressure_depth: NDArray[np.float64] = pressure.loc[
        pressure_time_series.index, config.depth_col
    ].to_numpy()
    return np.interp(usbl_time, pressure_time, pressure_depth)
