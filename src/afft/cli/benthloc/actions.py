"""Actions for Benthloc CLI commands."""

from pathlib import Path

from afft.benthloc import (
    BuildTelemetryIngestionDocumentCommand,
    BuildTelemetryIngestionDocumentResult,
    BuildTrajectoryIngestionDocumentCommand,
    BuildTrajectoryIngestionDocumentResult,
    TelemetryIngestionConfig,
    read_build_telemetry_ingestion_document_config,
    run_build_telemetry_ingestion_document,
    run_build_trajectory_ingestion_document,
)
from afft.utils.log import logger


def invoke_build_trajectory_ingestion_document(
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
    """Build a Benthloc trajectory ingestion document from a processed
    deployment bundle's trajectory geoframe."""
    command = BuildTrajectoryIngestionDocumentCommand(
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
    result: BuildTrajectoryIngestionDocumentResult = (
        run_build_trajectory_ingestion_document(command)
    )
    if dry_run:
        logger.info(
            f"dry run: would write {result.pose_count} pose(s) for platform "
            f"{result.platform_label!r}, deployment "
            f"{result.deployment_label!r}, trajectory "
            f"{result.trajectory_label!r} to {result.output_file}"
        )


def invoke_build_telemetry_ingestion_document(
    bundle_file: str | Path,
    config_file: str | Path,
    output_file: str | Path,
    overwrite: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Build a Benthloc telemetry ingestion document from a built deployment
    bundle."""
    config: TelemetryIngestionConfig = (
        read_build_telemetry_ingestion_document_config(Path(config_file))
    )
    command = BuildTelemetryIngestionDocumentCommand(
        bundle_file=Path(bundle_file),
        config_file=Path(config_file),
        output_file=Path(output_file),
        overwrite=overwrite,
        dry_run=dry_run,
        verbose=verbose,
    )
    result: BuildTelemetryIngestionDocumentResult = (
        run_build_telemetry_ingestion_document(command, config)
    )
    if dry_run:
        logger.info(
            f"dry run: would write {result.series_count} series "
            f"({result.sample_count} sample(s), "
            f"{result.dropped_sample_count} dropped) for "
            f"{result.sensor_count} sensor(s), platform "
            f"{result.platform_key!r}, deployment "
            f"{result.deployment_key!r} to {result.output_file}"
        )
