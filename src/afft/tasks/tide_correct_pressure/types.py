"""Data types for the tide correction task."""

import pandas as pd

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class TideCorrectCommand:
    reading_file: Path
    sealevel_file: Path
    output_file: Path
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class TideCorrectConfig:
    pressure_timestamp_col: str = "timestamp"
    pressure_timestamp_format: str | None = None
    pressure_depth_col: str = "depth"
    tide_timestamp_col: str = "datetime"
    tide_timestamp_format: str | None = None
    tide_sea_level_col: str = "sea_level"


@dataclass(slots=True, frozen=True)
class TideCorrectData:
    readings: pd.DataFrame
    sealevels: pd.DataFrame
