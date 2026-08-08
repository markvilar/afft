"""Configuration types for ACFR stereo camera processing."""

from pydantic import BaseModel, ConfigDict


class PairStereoImagesConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    left_suffix: str = "LC16"
    right_suffix: str = "RM16"
    label_col: str = "label"
    filename_col: str = "filename"
    trigger_col: str = "trigger_time"
    timestamp_col: str = "timestamp"
    max_offset_ms: float = 300.0
