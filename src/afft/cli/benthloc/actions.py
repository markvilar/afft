"""Actions for Benthloc CLI commands."""

from pathlib import Path

from afft.benthloc import (
    BuildTrajectoryIngestionFileCommand,
    BuildTrajectoryIngestionFileResult,
    run_build_trajectory_ingestion_file,
)
from afft.utils.log import logger


def invoke_build_trajectory_ingestion_file(
    bundle_file: str | Path,
    key: str,
    output_file: str | Path,
    trajectory_label: str,
    trajectory_description: str | None,
    timestamp_column: str,
    yaw_column: str,
    pitch_column: str,
    roll_column: str,
    platform_label: str | None,
    deployment_label: str | None,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Build a Benthloc trajectory ingestion file from a processed
    deployment bundle's trajectory geoframe."""
    command = BuildTrajectoryIngestionFileCommand(
        bundle_file=Path(bundle_file),
        key=key,
        output_file=Path(output_file),
        trajectory_label=trajectory_label,
        trajectory_description=trajectory_description,
        timestamp_column=timestamp_column,
        yaw_column=yaw_column,
        pitch_column=pitch_column,
        roll_column=roll_column,
        platform_label=platform_label,
        deployment_label=deployment_label,
        overwrite=overwrite,
        dry_run=dry_run,
    )
    result: BuildTrajectoryIngestionFileResult = (
        run_build_trajectory_ingestion_file(command)
    )
    if dry_run:
        logger.info(
            f"dry run: would write {result.pose_count} pose(s) for platform "
            f"{result.platform_label!r}, deployment "
            f"{result.deployment_label!r}, trajectory "
            f"{result.trajectory_label!r} to {result.output_file}"
        )
