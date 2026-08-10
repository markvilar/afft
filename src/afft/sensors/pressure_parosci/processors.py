"""Pressure sensor processors for Paroscientific instruments."""

import numpy as np
import pandas as pd

from numpy.typing import NDArray

from afft.utils.log import logger

from .types import PressureUncertaintyConfig, SeaLevelCorrectionConfig


def estimate_pressure_uncertainty(
    df: pd.DataFrame,
    config: PressureUncertaintyConfig = PressureUncertaintyConfig(),
) -> pd.DataFrame:
    """Add a depth_uncertainty column to a pressure sensor table.

    depth_uncertainty = base_uncertainty + depth_scale * depth

    With depth_scale=0.0 (default) the uncertainty is a constant noise floor.
    A non-zero depth_scale adds a depth-proportional term for sensors whose
    accuracy is specified as a percentage of reading.
    """
    result: pd.DataFrame = df.copy()
    result["depth_uncertainty"] = (
        config.base_uncertainty + config.depth_scale * result[config.depth_col]
    )
    return result


def correct_pressure_for_sea_level(
    pressure: pd.DataFrame,
    sea_level: pd.DataFrame,
    config: SeaLevelCorrectionConfig = SeaLevelCorrectionConfig(),
) -> pd.DataFrame:
    """
    Subtract the interpolated tide from a pressure frame's depth readings.

    Arguments
    ---------
    pressure: Pressure frame carrying a timestamp and a depth column.
    sea_level: Tide series carrying a timestamp and a sea level column.
    config: Column names and the coverage gap threshold.

    The sign convention is `corrected_depth = depth - sea_level`. Pressure
    depth is measured from the instantaneous water surface, so a fixed
    seabed point reads deeper at high tide, and subtracting the tide
    references the reading to a fixed datum. Regressing seabed depth on
    tide within a deployment gives a positive slope, which agrees.

    The tide series is assumed sorted by timestamp, which both the
    interpolation and the gap search rely on.

    Returns
    -------
    A copy of `pressure` with `sea_level` and `corrected_depth` added.

    Raises
    ------
    ValueError: If the sea level frame holds no rows.
    """
    if sea_level.empty:
        raise ValueError(
            "sea level frame holds no rows: nothing to interpolate from"
        )

    pressure_times: NDArray[np.int64] = (
        pressure[config.timestamp_col].astype(np.int64).to_numpy()
    )
    sea_level_times: NDArray[np.int64] = (
        sea_level[config.sea_level_timestamp_col].astype(np.int64).to_numpy()
    )

    _warn_on_coverage_gaps(pressure_times, sea_level_times, config)

    interpolated: NDArray[np.float64] = np.interp(
        pressure_times,
        sea_level_times,
        sea_level[config.sea_level_col].to_numpy(),
    )

    result: pd.DataFrame = pressure.copy()
    result["sea_level"] = interpolated
    result["corrected_depth"] = result[config.depth_col] - interpolated
    return result


def _warn_on_coverage_gaps(
    pressure_times: NDArray[np.int64],
    sea_level_times: NDArray[np.int64],
    config: SeaLevelCorrectionConfig,
) -> None:
    """Log a warning if any reading sits too far from a tide sample."""
    last: int = len(sea_level_times) - 1
    indices = np.searchsorted(sea_level_times, pressure_times)
    before = np.abs(
        pressure_times - sea_level_times[np.clip(indices - 1, 0, last)]
    )
    after = np.abs(pressure_times - sea_level_times[np.clip(indices, 0, last)])
    nearest = np.minimum(before, after)

    exceeds = nearest > int(config.max_gap_seconds * 1e9)
    if not exceeds.any():
        return

    logger.warning(
        f"{exceeds.sum()} of {len(pressure_times)} pressure readings are "
        f"further than {config.max_gap_seconds:.0f} s from a sea level "
        f"sample (largest gap {nearest.max() / 1e9:.0f} s); these are "
        f"clamped to the nearest end of the tide series, not extrapolated"
    )
