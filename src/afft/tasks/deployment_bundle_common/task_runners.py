"""Runners for the common deployment bundle tasks."""

from typing import Literal

import pandas as pd

from afft.deployment import DeploymentBundleIO, open_deployment_bundle
from afft.utils.log import logger

from .task_helpers import read_frame_file, validate_ingest_frame_input
from .task_types import IngestFrameCommand, IngestFrameResult


def run_ingest_frame(command: IngestFrameCommand) -> IngestFrameResult:
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
    validate_ingest_frame_input(command)

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

    return IngestFrameResult(
        bundle_file=command.bundle_file,
        key=command.key,
        rows=len(frame),
        columns=tuple(frame.columns),
    )
