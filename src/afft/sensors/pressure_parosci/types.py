"""Configuration types for Paroscientific pressure sensor processing."""

from pydantic import BaseModel, ConfigDict


class PressureUncertaintyConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_uncertainty: float = 0.005
    depth_scale: float = 0.0
    depth_col: str = "depth"
