"""Pressure sensor uncertainty processor for Paroscientific instruments."""

import pandas as pd

from afft.telemetry_processing.pipeline import register_processor

from .types import PressureUncertaintyConfig


@register_processor("estimate_pressure_uncertainty")
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
