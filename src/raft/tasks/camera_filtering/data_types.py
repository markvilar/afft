"""Module for camera filtering data types."""

import polars as pl

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CameraFilteringContext:
    """Class representing a camera filtering context."""

    camera_file: Path
    output_file: Path
    label_file: Optional[Path] = None

    @property
    def has_labels(self) -> bool:
        """Returns true if the context has a target file."""
        return isinstance(self.label_file, Path)


@dataclass
class CameraFilteringData:
    """Class representing camera filtering data."""

    cameras: pl.DataFrame
    labels: Optional[list[str]] = None

    @property
    def has_labels(self) -> bool:
        """Returns true if the data contains camera labels."""
        return isinstance(self.labels, list)
