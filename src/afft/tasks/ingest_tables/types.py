"""Data types for the table ingestion task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class IngestTablesCommand:
    source_dir: Path
    pattern: str = "*.csv"
    overwrite: bool = False
    verbose: bool = False
    timestamp_columns: tuple[str, ...] = ("timestamp",)


@dataclass(slots=True, frozen=True)
class IngestTableResult:
    file: Path
    table: str
    rows: int
