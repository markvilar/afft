"""Data types for the table clipping task."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ClipTablesCommand:
    source_dir: Path
    output_dir: Path
    start: datetime
    end: datetime
    pattern: str = "*.csv"
    timestamp_column: str = "timestamp"


@dataclass(slots=True, frozen=True)
class ClipTableResult:
    file: Path
    table: str
    rows_in: int
    rows_out: int
