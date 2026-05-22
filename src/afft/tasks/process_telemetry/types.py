"""Data types for the process telemetry task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ProcessTelemetryCommand:
    source_dir: Path
    output_dir: Path
    config_file: Path
    pattern: str = "*.csv"
