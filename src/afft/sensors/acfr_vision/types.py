"""Configuration types for ACFR stereo camera processing."""

from dataclasses import dataclass

import pandas as pd

from pydantic import BaseModel, ConfigDict


class StereoPairingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    left_suffix: str = "LC16"
    right_suffix: str = "RM16"
    label_col: str = "label"
    filename_col: str = "filename"
    trigger_col: str = "trigger_time"
    timestamp_col: str = "timestamp"
    max_offset_ms: float = 300.0


@dataclass(slots=True, frozen=True)
class StereoPairingResult:
    """
    A stereo pairing run's output frame and what it discarded.

    Attributes
    ----------
    frame: One row per paired trigger.
    left_total: Left images seen before matching.
    right_total: Right images seen before matching.
    left_unmatched: Left images dropped for having no right counterpart.
    right_unmatched: Right images dropped for having no left counterpart.
    """

    frame: pd.DataFrame
    left_total: int
    right_total: int
    left_unmatched: int
    right_unmatched: int
