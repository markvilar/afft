"""Pressure sensor uncertainty processor."""

from dataclasses import dataclass

import pandas as pd

from .pipeline import register_processor


@dataclass(slots=True, frozen=True)
class PressureUncertaintyConfig:
    base_uncertainty: float = 0.005
    depth_scale: float = 0.0
    depth_col: str = "depth"


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
