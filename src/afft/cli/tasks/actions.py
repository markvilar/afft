"""Actions for data processing task CLI commands."""

from datetime import datetime
from pathlib import Path

from afft.tasks.clip_tables import ClipTablesCommand, run_clip_tables
from afft.tasks.collect_renav_stereo_poses import (
    CollectRenavStereoPosesCommand,
    run_collect_renav_stereo_poses,
)
from afft.tasks.process_renav import ProcessRenavCommand, run_process_renav
from afft.tasks.process_telemetry import (
    GroupingStrategy,
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
    grouping_strategy: str = "prefix",
) -> None:
    """Dispatch the telemetry processing pipeline task."""
    command = ProcessTelemetryCommand(
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
        config_file=Path(config_file),
        pattern=pattern,
        strategy=GroupingStrategy(grouping_strategy),
    )
    run_process_telemetry(command)


def dispatch_collect_renav_stereo_poses(
    root_dir: str | Path,
    output_dir: str | Path,
    deployment_suffix: str = "_deployment_data",
    appendix: str = "_renav_stereo_poses.txt",
    tiebreak_margin: float = 0.03,
) -> None:
    """Collect and relabel Renav stereo pose estimate files by deployment."""
    command = CollectRenavStereoPosesCommand(
        root_dir=Path(root_dir),
        output_dir=Path(output_dir),
        deployment_suffix=deployment_suffix,
        appendix=appendix,
        tiebreak_margin=tiebreak_margin,
    )
    run_collect_renav_stereo_poses(command)


def dispatch_process_renav(
    input_file: str | Path,
    output_file: str | Path,
) -> None:
    """Process a Renav stereo pose estimate file and write to CSV."""
    command = ProcessRenavCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
    )
    run_process_renav(command)


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
