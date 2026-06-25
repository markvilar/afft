"""Data types for the process telemetry task."""

from dataclasses import dataclass
from pathlib import Path

from .grouping import GroupingStrategy


@dataclass(slots=True, frozen=True)
class ProcessTelemetryCommand:
    source_dir: Path
    output_dir: Path
    config_file: Path
    pattern: str = "*.csv"
    strategy: GroupingStrategy = GroupingStrategy.PREFIX
    timestamp_column: str = "timestamp"
    timestamp_format: str = "ISO8601"
