"""Configuration types for Paroscientific pressure sensor processing."""

from pydantic import BaseModel, ConfigDict


class PressureUncertaintyConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_uncertainty: float = 0.005
    depth_scale: float = 0.0
    depth_col: str = "depth"


class SeaLevelCorrectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    depth_col: str = "depth"
    timestamp_col: str = "timestamp"
    sea_level_col: str = "sea_level"
    sea_level_timestamp_col: str = "timestamp"
    max_gap_seconds: float = 3600.0
