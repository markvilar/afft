"""DVL uncertainty processor."""

from dataclasses import dataclass

import pandas as pd

from .pipeline import register_processor


@dataclass(slots=True, frozen=True)
class DvlUncertaintyConfig:
    # Per-axis velocity uncertainty (m/s). RDI spec: 0.3 cm/s at 1 m/s.
    velocity_x_uncertainty: float = 0.003
    velocity_y_uncertainty: float = 0.003
    velocity_z_uncertainty: float = 0.003
    # Per-axis attitude uncertainty (degrees). RDI spec: 0.25 deg roll/pitch, 1.0 deg heading.
    roll_uncertainty: float = 0.25
    pitch_uncertainty: float = 0.25
    heading_uncertainty: float = 1.0
    # Column names in the input DataFrame
    velocity_x_col: str = "velocity_x"
    velocity_y_col: str = "velocity_y"
    velocity_z_col: str = "velocity_z"


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
