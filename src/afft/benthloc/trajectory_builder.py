"""Builder for the Benthloc trajectory ingestion file: reads a processed
deployment bundle's trajectory geoframe and writes the GeoJSON
`FeatureCollection` Benthloc's `trajectory_ingestion` task reads."""

import geopandas as gpd
import pandas as pd

from afft.deployment import (
    DeploymentBundleReader,
    open_deployment_bundle_reader,
)
from afft.utils.log import logger

from .common_types import ResolvedIdentity, resolve_identity
from .common_writers import write_feature_collection_file
from .trajectory_types import (
    BuildTrajectoryIngestionFileCommand,
    BuildTrajectoryIngestionFileResult,
)
from .trajectory_validators import validate_trajectory_geoframe


def validate_build_trajectory_ingestion_file_input(
    command: BuildTrajectoryIngestionFileCommand,
) -> None:
    """
    Validate the task's inputs before any expensive work runs.

    Arguments
    ---------
    command: Task command.

    Raises
    ------
    FileNotFoundError: If the bundle file or the output directory does not
        exist.
    FileExistsError: If the output file already exists, `overwrite` is not
        set, and the run is not a `dry_run`.
    """
    if not command.bundle_file.is_file():
        raise FileNotFoundError(
            f"bundle file does not exist: {command.bundle_file}"
        )

    if not command.output_file.parent.is_dir():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    if (
        not command.dry_run
        and command.output_file.exists()
        and not command.overwrite
    ):
        raise FileExistsError(
            f"output file already exists: {command.output_file}"
        )


def _build_output_frame(
    frame: gpd.GeoDataFrame,
    command: BuildTrajectoryIngestionFileCommand,
    identity: ResolvedIdentity,
) -> gpd.GeoDataFrame:
    """Select, rename, and attach identity/trajectory fields onto the
    validated source geoframe, producing Benthloc's exact property set."""
    return gpd.GeoDataFrame(
        {
            "timestamp": frame[command.timestamp_column],
            "platform_label": identity.platform_label,
            "deployment_label": identity.deployment_label,
            "trajectory_label": command.trajectory_label,
            "trajectory_description": command.trajectory_description,
            "yaw": frame[command.yaw_column],
            "pitch": frame[command.pitch_column],
            "roll": frame[command.roll_column],
        },
        geometry=frame.geometry,
        crs=frame.crs,
    )


def run_build_trajectory_ingestion_file(
    command: BuildTrajectoryIngestionFileCommand,
) -> BuildTrajectoryIngestionFileResult:
    """
    Build a Benthloc trajectory ingestion file from a processed deployment
    bundle's trajectory geoframe.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The run's result, naming the resolved labels and pose count.

    Raises
    ------
    FileNotFoundError: If the bundle file or the output directory does not
        exist.
    FileExistsError: If the output file already exists, `overwrite` is not
        set, and the run is not a `dry_run`.
    ValueError: If the bundle holds no frame at `command.key`, if that key's
        geoframe fails validation, or if no poses remain after dropping
        incomplete rows.
    TypeError: If `command.key` does not hold a geoframe.
    KeyError: If a required column is absent from the source geoframe, or an
        identity label has no override and the bundle holds no identity
        frame to read it from.
    """
    validate_build_trajectory_ingestion_file_input(command)

    reader: DeploymentBundleReader
    with open_deployment_bundle_reader(command.bundle_file) as reader:
        if not reader.has_frame(command.key):
            raise ValueError(
                f"bundle holds no frame at {command.key!r}: "
                f"{command.bundle_file} holds "
                f"{sorted(set(reader.list_frames()) | set(reader.list_geoframes()))}"
            )
        if not reader.is_geoframe(command.key):
            raise TypeError(
                f"bundle key {command.key!r} does not hold a geoframe, "
                f"required for trajectory ingestion"
            )
        source: gpd.GeoDataFrame = reader.read_geoframe(command.key)
        identity: ResolvedIdentity = resolve_identity(
            reader, command.platform_label, command.deployment_label
        )

    cleaned, dropped = validate_trajectory_geoframe(source, command)
    output_frame: gpd.GeoDataFrame = _build_output_frame(
        cleaned, command, identity
    )

    timestamps: pd.Series = output_frame["timestamp"]
    start: pd.Timestamp = timestamps.min()
    end: pd.Timestamp = timestamps.max()

    logger.info("-------------------------------------")
    logger.info("Build Trajectory Ingestion File")
    logger.info(f"  bundle file:  {command.bundle_file}")
    logger.info(f"  key:          {command.key}")
    logger.info(f"  output file:  {command.output_file}")
    logger.info(f"  platform:     {identity.platform_label}")
    logger.info(f"  deployment:   {identity.deployment_label}")
    logger.info(f"  trajectory:   {command.trajectory_label}")
    logger.info(f"  poses:        {len(output_frame)}")
    logger.info(f"  dropped:      {dropped}")
    logger.info("-------------------------------------")

    if not command.dry_run:
        write_feature_collection_file(
            output_frame, command.output_file, overwrite=command.overwrite
        )
        logger.info(f"wrote trajectory ingestion file to {command.output_file}")

    return BuildTrajectoryIngestionFileResult(
        output_file=command.output_file,
        platform_label=identity.platform_label,
        deployment_label=identity.deployment_label,
        trajectory_label=command.trajectory_label,
        pose_count=len(output_frame),
        dropped_row_count=dropped,
        start_timestamp=start.to_pydatetime(),
        end_timestamp=end.to_pydatetime(),
        written=not command.dry_run,
    )
