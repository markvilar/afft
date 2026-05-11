"""Actions for data processing task CLI commands."""

from pathlib import Path

from afft.tasks.tide_correct_pressure import (
    TideCorrectCommand,
    TideCorrectConfig,
    run_tide_correction,
)


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
