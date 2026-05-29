"""DVL uncertainty processor for Teledyne instruments."""

import pandas as pd

from afft.telemetry_processing.pipeline import register_processor

from .types import DvlUncertaintyConfig


@register_processor("estimate_dvl_uncertainty")
def estimate_dvl_uncertainty(
    df: pd.DataFrame,
    config: DvlUncertaintyConfig = DvlUncertaintyConfig(),
) -> pd.DataFrame:
    """Add per-axis velocity and attitude uncertainty columns to a DVL table.

    All uncertainty values are constants taken from the sensor specification.
    Velocity uncertainties are in m/s; attitude uncertainties are in degrees.
    """
    result: pd.DataFrame = df.copy()

    result["velocity_x_uncertainty"] = config.velocity_x_uncertainty
    result["velocity_y_uncertainty"] = config.velocity_y_uncertainty
    result["velocity_z_uncertainty"] = config.velocity_z_uncertainty
    result["roll_uncertainty"] = config.roll_uncertainty
    result["pitch_uncertainty"] = config.pitch_uncertainty
    result["heading_uncertainty"] = config.heading_uncertainty

    return result
