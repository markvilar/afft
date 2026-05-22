"""Actions for data processing task CLI commands."""

from datetime import datetime
from pathlib import Path

from afft.tasks.clip_tables import ClipTablesCommand, run_clip_tables
from afft.tasks.process_telemetry import (
    ProcessTelemetryCommand,
    run_process_telemetry,
)
from afft.tasks.tide_correct_pressure import (
    TideCorrectCommand,
    TideCorrectConfig,
    run_tide_correction,
)


def dispatch_clip_tables(
    source_dir: str | Path,
    output_dir: str | Path,
    start: datetime,
    end: datetime,
    pattern: str = "*.csv",
    timestamp_column: str = "timestamp",
) -> None:
    """Clip rows in CSV files to the [start, end] time interval."""
    command = ClipTablesCommand(
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
        start=start,
        end=end,
        pattern=pattern,
        timestamp_column=timestamp_column,
    )
    run_clip_tables(command)


def dispatch_process_telemetry(
    source_dir: str | Path,
    output_dir: str | Path,
    config_file: str | Path,
    pattern: str = "*.csv",
) -> None:
    """Dispatch the telemetry processing pipeline task."""
    command = ProcessTelemetryCommand(
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
        config_file=Path(config_file),
        pattern=pattern,
    )
    run_process_telemetry(command)


def dispatch_correct_pressure_tide(
    reading_file: str | Path,
    sealevel_file: str | Path,
    output_file: str | Path,
    verbose: bool = False,
) -> None:
    """Dispatch the tide correction task with default column configuration."""
    command = TideCorrectCommand(
        reading_file=Path(reading_file),
        sealevel_file=Path(sealevel_file),
        output_file=Path(output_file),
        verbose=verbose,
    )
    config = TideCorrectConfig()
    run_tide_correction(command, config)
