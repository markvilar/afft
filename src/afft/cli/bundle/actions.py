"""Actions for deployment bundle CLI commands."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from afft.deployment import (
    decode_frame_dtypes,
    open_deployment_bundle_reader,
)
from afft.utils.log import logger

from afft.tasks.build_deployment_bundle import (
    BuildDeploymentBundleCommand,
    read_build_deployment_bundle_config,
    run_build_deployment_bundle,
)
from afft.tasks.deployment_bundle_common import (
    ClipDeploymentBundleCommand,
    ExportBundleFrameCommand,
    IngestBundleFrameCommand,
    run_clip_deployment_bundle,
    run_export_bundle_frame,
    run_ingest_bundle_frame,
)
from afft.tasks.process_deployment_bundle import (
    ProcessDeploymentBundleCommand,
    run_process_deployment_bundle,
)


def invoke_build_deployment_bundle(
    descriptor_file: str | Path,
    deployment_label: str,
    data_dir: str | Path,
    config_file: str | Path,
    output_file: str | Path,
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Build a deployment bundle from a descriptor and its raw message logs."""
    command = BuildDeploymentBundleCommand(
        descriptor_file=Path(descriptor_file),
        deployment_label=deployment_label,
        data_dir=Path(data_dir),
        config_file=Path(config_file),
        output_file=Path(output_file),
        overwrite=overwrite,
        verbose=verbose,
    )
    config = read_build_deployment_bundle_config(command.config_file)
    run_build_deployment_bundle(command, config)


def invoke_list_deployment_bundle(
    input_file: str | Path,
    dtypes: bool = False,
) -> None:
    """
    List the frames a deployment bundle holds, as recorded in its
    `bundle_contents` manifest.

    Arguments
    ---------
    input_file: Path to the deployment bundle to list.
    dtypes: Also log each frame's recorded column dtypes.
    """
    input_file = Path(input_file)
    with open_deployment_bundle_reader(input_file) as reader:
        contents: pd.DataFrame = reader.contents()

    logger.info("-------------------------------------")
    logger.info("Deployment Bundle Contents")
    logger.info(f"  input file: {input_file}")
    logger.info(f"  frames:     {len(contents)}")
    logger.info("-------------------------------------")

    for row in contents.itertuples(index=False):
        logger.info(f"{row.identifier}")
        if row.table_name != row.identifier:
            logger.info(f"  table: {row.table_name}")
        if dtypes:
            for column, dtype in decode_frame_dtypes(row.dtypes).items():
                logger.info(f"  {column}: {dtype}")


def invoke_ingest_bundle_frame(
    bundle_file: str | Path,
    key: str,
    input_file: str | Path,
    datetime_columns: tuple[str, ...] = (),
    overwrite: bool = False,
) -> None:
    """Ingest a frame from a file into an existing deployment bundle."""
    command = IngestBundleFrameCommand(
        bundle_file=Path(bundle_file),
        key=key,
        input_file=Path(input_file),
        datetime_columns=datetime_columns,
        overwrite=overwrite,
    )
    run_ingest_bundle_frame(command)


def invoke_export_bundle_frame(
    bundle_file: str | Path,
    key: str,
    output_file: str | Path,
    overwrite: bool = False,
) -> None:
    """Export a single frame from a deployment bundle to a file."""
    command = ExportBundleFrameCommand(
        bundle_file=Path(bundle_file),
        key=key,
        output_file=Path(output_file),
        overwrite=overwrite,
    )
    run_export_bundle_frame(command)


def invoke_process_deployment_bundle(
    input_file: str | Path,
    config_file: str | Path,
    output_file: str | Path,
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Run the configured processing pipeline over a deployment bundle."""
    command = ProcessDeploymentBundleCommand(
        input_file=input_file,
        config_file=config_file,
        output_file=output_file,
        overwrite=overwrite,
        verbose=verbose,
    )
    run_process_deployment_bundle(command)


def invoke_clip_deployment_bundle(
    input_file: str | Path,
    output_file: str | Path,
    start: datetime,
    end: datetime,
    label_suffix: str,
    datetime_column: str = "timestamp",
    no_clip_patterns: tuple[str, ...] = (),
    overwrite: bool = False,
) -> None:
    """Clip a deployment bundle's tables to a temporal window."""
    command = ClipDeploymentBundleCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
        start=start,
        end=end,
        label_suffix=label_suffix,
        datetime_column=datetime_column,
        no_clip_patterns=no_clip_patterns,
        overwrite=overwrite,
    )
    run_clip_deployment_bundle(command)
