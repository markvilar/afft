"""Configuration types for Paroscientific pressure sensor processing."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PressureUncertaintyConfig:
    base_uncertainty: float = 0.005
    depth_scale: float = 0.0
    depth_col: str = "depth"
