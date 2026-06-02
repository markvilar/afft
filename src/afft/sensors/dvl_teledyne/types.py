"""Configuration types for Teledyne DVL processing."""

from dataclasses import dataclass


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
