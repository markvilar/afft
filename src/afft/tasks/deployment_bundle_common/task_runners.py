"""Runners for the common deployment bundle tasks."""

from typing import Literal

import pandas as pd

from afft.deployment import (
    DeploymentBundleIO,
    DeploymentBundleReader,
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.utils.log import logger

from .task_helpers import (
    read_frame_file,
    validate_export_bundle_frame_input,
    validate_ingest_bundle_frame_input,
    write_frame_file,
)
from .task_types import (
    ExportBundleFrameCommand,
    ExportBundleFrameResult,
    IngestBundleFrameCommand,
    IngestBundleFrameResult,
)


def run_export_bundle_frame(
    command: ExportBundleFrameCommand,
) -> ExportBundleFrameResult:
    """
    Export a single frame from a deployment bundle to a file.

    The bundle is opened through the reader interface and is never written,
    so an export cannot damage the bundle it reads.

    A key the bundle does not hold raises, and the message names the keys
    it does. Getting the key wrong is the expected user error here -- they
    are long, layered, and vary by deployment -- and a bare "no frame at
    that key" turns a typo into a round trip through ``afft bundle list``.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The run's result, naming the file written and the frame's shape.

    Raises
    ------
    FileNotFoundError: If the bundle does not exist.
    FileExistsError: If the output file exists and ``overwrite`` is not set.
    ValueError: If the frame key is not structurally valid, if the output
        file's suffix does not name a supported format, or if the bundle
        holds no frame at the key.
    """
    validate_export_bundle_frame_input(command)

    reader: DeploymentBundleReader
    with open_deployment_bundle_reader(command.bundle_file) as reader:
        if not reader.has_frame(command.key):
            raise ValueError(
                f"bundle holds no frame at {command.key!r}: "
                f"{command.bundle_file} holds {sorted(reader.list_frames())}"
            )
        frame: pd.DataFrame = reader.read_frame(command.key)

    logger.info("-------------------------------------")
    logger.info("Export Frame")
    logger.info(f"  bundle file: {command.bundle_file}")
    logger.info(f"  key:         {command.key}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  rows:        {len(frame)}")
    logger.info("-------------------------------------")

    command.output_file.parent.mkdir(parents=True, exist_ok=True)
    write_frame_file(frame, command.output_file)

    logger.info(f"wrote {command.key} to {command.output_file}")

    return ExportBundleFrameResult(
        output_file=command.output_file,
        key=command.key,
        rows=len(frame),
        columns=tuple(frame.columns),
    )


def run_ingest_bundle_frame(
    command: IngestBundleFrameCommand,
) -> IngestBundleFrameResult:
    """
    Ingest a frame from a file into an existing deployment bundle.

    The bundle is written in place. This is a deliberate exception to the
    build-don't-mutate rule the processing pipeline follows: ingestion
    deposits data that already exists rather than deriving anything, so
    copying a whole bundle forward per ingested frame would buy nothing.

    Only the frame and its ``bundle_contents`` entry are written. The file
    inventory and provenance layers are left alone -- an ingested frame is
    a frame, not a change to what the bundle claims about the deployment.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The run's result, naming the key written and the frame's shape.

    Raises
    ------
    FileNotFoundError: If the bundle or the input file does not exist.
    ValueError: If the frame key is not structurally valid, if a named
        datetime column is not in the input file, or if the key already
        holds a frame and ``overwrite`` is not set.
    """
    validate_ingest_bundle_frame_input(command)

    frame: pd.DataFrame = read_frame_file(
        command.input_file, command.datetime_columns
    )

    logger.info("-------------------------------------")
    logger.info("Ingest Frame")
    logger.info(f"  bundle file: {command.bundle_file}")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  key:         {command.key}")
    logger.info(f"  rows:        {len(frame)}")
    logger.info("-------------------------------------")

    if_exists: Literal["fail", "replace"] = (
        "replace" if command.overwrite else "fail"
    )

    bundle: DeploymentBundleIO
    with open_deployment_bundle(command.bundle_file) as bundle:
        if bundle.has_frame(command.key) and not command.overwrite:
            raise ValueError(
                f"bundle already holds a frame at {command.key!r}: "
                f"pass overwrite to replace it"
            )
        bundle.write_frame(command.key, frame, if_exists=if_exists)

    logger.info(f"wrote {command.key} to {command.bundle_file}")

    return IngestBundleFrameResult(
        bundle_file=command.bundle_file,
        key=command.key,
        rows=len(frame),
        columns=tuple(frame.columns),
    )
