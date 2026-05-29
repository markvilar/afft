"""Position resolution, uncertainty, and orchestration for TrackLink USBL."""

import numpy as np
import pandas as pd

from afft.telemetry_processing.pipeline import register_processor

from .types import (
    UsblProcessingConfig,
    UsblResolvePositionConfig,
    UsblUncertaintyConfig,
)

_EARTH_RADIUS_M: float = 6_371_000.0


@register_processor("resolve_usbl_position")
def resolve_usbl_position(
    usbl: pd.DataFrame,
    pressure: pd.DataFrame,
    config: UsblResolvePositionConfig = UsblResolvePositionConfig(),
) -> pd.DataFrame:
    """Resolve AUV lat/lon from TrackLink USBL bearing, slant range, and depth.

    Depth from the pressure DataFrame is interpolated to USBL timestamps.
    Horizontal range is computed as sqrt(slant_range² - depth²).
    The AUV position is projected from the ship position along the bearing
    using a spherical-Earth forward geodesic.

    bearing_reference: "absolute" treats bearing as a compass bearing (default);
    "relative" adds ship heading to obtain the compass bearing first.

    Adds columns: interpolated_depth, horizontal_range,
                  target_latitude, target_longitude.
    """
    result: pd.DataFrame = usbl.copy()

    usbl_t: np.ndarray = (
        pd.to_datetime(result[config.timestamp_col]).astype(np.int64).to_numpy()
    )

    pressure_t_series: pd.Series = pd.to_datetime(
        pressure[config.timestamp_col]
    ).sort_values()
    pressure_depth: np.ndarray = pressure.loc[
        pressure_t_series.index, config.depth_col
    ].to_numpy()
    pressure_t: np.ndarray = pressure_t_series.astype(np.int64).to_numpy()

    depth: np.ndarray = np.interp(usbl_t, pressure_t, pressure_depth)

    if config.bearing_reference == "relative":
        bearing: pd.Series = (
            result[config.bearing_col] + result[config.ship_heading_col]
        ) % 360.0
    else:
        bearing = result[config.bearing_col]

    slant_range: np.ndarray = result[config.range_col].to_numpy()
    horizontal_range: np.ndarray = np.sqrt(
        np.maximum(slant_range**2 - depth**2, 0.0)
    )

    lat1: np.ndarray = np.radians(result[config.ship_lat_col].to_numpy())
    lon1: np.ndarray = np.radians(result[config.ship_lon_col].to_numpy())
    bearing_rad: np.ndarray = np.radians(bearing.to_numpy())
    d_over_r: np.ndarray = horizontal_range / _EARTH_RADIUS_M

    lat2: np.ndarray = np.arcsin(
        np.sin(lat1) * np.cos(d_over_r)
        + np.cos(lat1) * np.sin(d_over_r) * np.cos(bearing_rad)
    )
    lon2: np.ndarray = lon1 + np.arctan2(
        np.sin(bearing_rad) * np.sin(d_over_r) * np.cos(lat1),
        np.cos(d_over_r) - np.sin(lat1) * np.sin(lat2),
    )

    result["interpolated_depth"] = depth
    result["horizontal_range"] = horizontal_range
    result["target_latitude"] = np.degrees(lat2)
    result["target_longitude"] = np.degrees(lon2)

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

    slant_range: np.ndarray = result[config.range_col].to_numpy()
    horizontal_range: np.ndarray = result[
        config.horizontal_range_col
    ].to_numpy()
    bearing_uncertainty_rad: float = np.radians(config.bearing_uncertainty)

    h_safe: np.ndarray = np.maximum(
        horizontal_range, config.min_horizontal_range
    )
    range_term: np.ndarray = config.range_uncertainty * slant_range / h_safe
    bearing_term: np.ndarray = horizontal_range * bearing_uncertainty_rad

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
