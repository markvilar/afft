"""Runners for the common deployment bundle tasks."""

import os

from datetime import datetime
from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd

from afft.deployment import (
    DeploymentBundleIO,
    DeploymentBundleReader,
    DeploymentIdentity,
    DeploymentProvenance,
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.tasks.build_deployment_bundle import record_to_frame
from afft.utils.log import logger

from .task_helpers import (
    clip_frame_to_window,
    is_geoframe_suffix,
    key_matches_no_clip,
    read_frame_file,
    read_geoframe_file,
    validate_clip_deployment_bundle_input,
    validate_export_bundle_frame_input,
    validate_ingest_bundle_frame_input,
    write_frame_file,
    write_geoframe_file,
)
from .task_types import (
    ClipDeploymentBundleCommand,
    ClipDeploymentBundleResult,
    ClippedFrame,
    ExportBundleFrameCommand,
    ExportBundleFrameResult,
    IngestBundleFrameCommand,
    IngestBundleFrameResult,
)

_IDENTITY_KEY: str = "deployment/identity"
_PROVENANCE_KEY: str = "deployment/provenance"


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
        file's suffix does not name a supported format, if the bundle holds
        no frame at the key, or if the key holds a geoframe and the output
        file's suffix does not name a geodata format.
    """
    validate_export_bundle_frame_input(command)

    reader: DeploymentBundleReader
    with open_deployment_bundle_reader(command.bundle_file) as reader:
        if not reader.has_frame(command.key):
            raise ValueError(
                f"bundle holds no frame at {command.key!r}: "
                f"{command.bundle_file} holds "
                f"{sorted(set(reader.list_frames()) | set(reader.list_geoframes()))}"
            )
        is_geoframe: bool = reader.is_geoframe(command.key)
        if is_geoframe and not is_geoframe_suffix(command.output_file.suffix):
            raise ValueError(
                f"{command.key!r} holds a geoframe, which cannot be "
                f"exported to {command.output_file.suffix!r}: "
                f"{command.output_file}"
            )

        if is_geoframe:
            geoframe: gpd.GeoDataFrame = reader.read_geoframe(command.key)
            rows, columns = len(geoframe), tuple(geoframe.columns)
        else:
            frame: pd.DataFrame = reader.read_frame(command.key)
            rows, columns = len(frame), tuple(frame.columns)

    logger.info("-------------------------------------")
    logger.info("Export Frame")
    logger.info(f"  bundle file: {command.bundle_file}")
    logger.info(f"  key:         {command.key}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  rows:        {rows}")
    logger.info("-------------------------------------")

    command.output_file.parent.mkdir(parents=True, exist_ok=True)
    if is_geoframe:
        write_geoframe_file(geoframe, command.output_file)
    else:
        write_frame_file(frame, command.output_file)

    logger.info(f"wrote {command.key} to {command.output_file}")

    return ExportBundleFrameResult(
        output_file=command.output_file,
        key=command.key,
        rows=rows,
        columns=columns,
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

    is_geoframe: bool = is_geoframe_suffix(command.input_file.suffix)
    geoframe: gpd.GeoDataFrame
    frame: pd.DataFrame
    if is_geoframe:
        geoframe = read_geoframe_file(command.input_file)
        rows, columns = len(geoframe), tuple(geoframe.columns)
    else:
        frame = read_frame_file(command.input_file, command.datetime_columns)
        rows, columns = len(frame), tuple(frame.columns)

    logger.info("-------------------------------------")
    logger.info("Ingest Frame")
    logger.info(f"  bundle file: {command.bundle_file}")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  key:         {command.key}")
    logger.info(f"  rows:        {rows}")
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
        if is_geoframe:
            bundle.write_geoframe(command.key, geoframe, if_exists=if_exists)
        else:
            bundle.write_frame(command.key, frame, if_exists=if_exists)

    logger.info(f"wrote {command.key} to {command.bundle_file}")

    return IngestBundleFrameResult(
        bundle_file=command.bundle_file,
        key=command.key,
        rows=rows,
        columns=columns,
    )


def _clip_or_copy(
    key: str,
    frame: pd.DataFrame,
    target: DeploymentBundleIO,
    no_clip_patterns: tuple[str, ...],
    datetime_column: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    copied: list[str],
    clipped: list[ClippedFrame],
    empty: list[str],
) -> None:
    """
    Clip `frame` to the window, or copy it whole, and write the result to
    `target`, recording what happened into `copied`/`clipped`/`empty`.

    A frame matching a no-clip pattern, or lacking `datetime_column`, is
    copied whole. Otherwise it is clipped via `clip_frame_to_window`.

    A geoframe clipped to zero rows is written through `write_frame` rather
    than `write_geoframe`: `write_geoframe`'s validation rejects a frame
    whose geometry is entirely empty, which a zero-row result always is, and
    this task's contract keeps every source key in the output even when a
    window clips it to nothing. `write_frame` round-trips an empty
    `GeoDataFrame`'s geometry column and CRS the same as `write_geoframe`
    would, so nothing is lost by skipping the validation.

    Arguments
    ---------
    key: Bundle key `frame` was read from.
    frame: Frame to clip or copy; not mutated.
    target: Bundle the result is written to.
    no_clip_patterns: Key patterns whose frames are copied whole.
    datetime_column: Column to clip on.
    start: Start of the window, inclusive.
    end: End of the window, inclusive.
    copied: Appended with `key` if it is copied whole.
    clipped: Appended with a `ClippedFrame` if it is clipped.
    empty: Appended with `key` if the clipped result holds no rows.
    """
    is_geoframe: bool = isinstance(frame, gpd.GeoDataFrame)

    if (
        key_matches_no_clip(key, no_clip_patterns)
        or datetime_column not in frame.columns
    ):
        if is_geoframe:
            target.write_geoframe(key, frame, if_exists="fail")
        else:
            target.write_frame(key, frame, if_exists="fail")
        copied.append(key)
        return

    result: pd.DataFrame = clip_frame_to_window(
        key, frame, datetime_column, start, end
    )
    if is_geoframe and not result.empty:
        target.write_geoframe(key, result, if_exists="fail")
    else:
        target.write_frame(key, result, if_exists="fail")
    clipped.append(
        ClippedFrame(key=key, rows_before=len(frame), rows_after=len(result))
    )
    if result.empty:
        empty.append(key)
        logger.warning(f"{key}: no rows inside the clip window")


def run_clip_deployment_bundle(
    command: ClipDeploymentBundleCommand,
) -> ClipDeploymentBundleResult:
    """
    Clip a deployment bundle's tables to a temporal window, writing a new
    bundle.

    The input is opened through the reader interface and is never written, so
    a clip cannot damage the bundle it reads.

    The window is closed, ``start <= t <= end``. Cutting one source into
    adjacent windows therefore repeats the row on a shared bound in both
    clips, so windows meant to partition a deployment have to be stated so
    they do not touch.

    Every key the source holds is present in the output, including one the
    window clipped to zero rows. An empty telemetry table is an honest
    statement that the sensor produced nothing in the window, and keeping the
    key means a consumer's ``has_frame`` answers the same against both
    bundles.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The run's result, naming the clipped deployment and what happened to each
    key.

    Raises
    ------
    FileNotFoundError: If the input bundle does not exist.
    ValueError: If the output file is the input file, if it exists and
        ``overwrite`` is not set, if ``start`` is not before ``end``, or if
        ``label_suffix`` is empty.
    """
    validate_clip_deployment_bundle_input(command)

    start: pd.Timestamp = _to_utc_timestamp(command.start)
    end: pd.Timestamp = _to_utc_timestamp(command.end)

    logger.info("-------------------------------------")
    logger.info("Clip Deployment Bundle")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  window:      [{start.isoformat()}, {end.isoformat()}]")
    logger.info("-------------------------------------")

    clipped: list[ClippedFrame] = []
    copied: list[str] = []
    empty: list[str] = []
    deployment_label: str

    output_file: Path = command.output_file
    staged: Path = output_file.with_suffix(".partial" + output_file.suffix)
    try:
        reader: DeploymentBundleReader
        target: DeploymentBundleIO
        with open_deployment_bundle_reader(command.input_file) as reader:
            deployment_label = _clipped_deployment_label(
                reader, command.label_suffix
            )
            with open_deployment_bundle(staged) as target:
                for key in sorted(reader.list_frames()):
                    if key == _IDENTITY_KEY:
                        target.write_frame(
                            key,
                            record_to_frame(
                                DeploymentIdentity(
                                    deployment_label=deployment_label,
                                    deployment_start_datetime=command.start,
                                    deployment_end_datetime=command.end,
                                )
                            ),
                            if_exists="fail",
                        )
                        copied.append(key)
                        continue

                    if key == _PROVENANCE_KEY:
                        target.write_frame(
                            key,
                            record_to_frame(
                                DeploymentProvenance(
                                    deployment_key=deployment_label,
                                    source_bundle=str(command.input_file),
                                    clip_start_datetime=command.start,
                                    clip_end_datetime=command.end,
                                )
                            ),
                            if_exists="fail",
                        )
                        copied.append(key)
                        continue

                    _clip_or_copy(
                        key,
                        reader.read_frame(key),
                        target,
                        command.no_clip_patterns,
                        command.datetime_column,
                        start,
                        end,
                        copied,
                        clipped,
                        empty,
                    )

                for key in sorted(reader.list_geoframes()):
                    _clip_or_copy(
                        key,
                        reader.read_geoframe(key),
                        target,
                        command.no_clip_patterns,
                        command.datetime_column,
                        start,
                        end,
                        copied,
                        clipped,
                        empty,
                    )
        os.replace(staged, output_file)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise

    logger.info(f"wrote clipped deployment bundle to {output_file}")

    return ClipDeploymentBundleResult(
        input_file=command.input_file,
        output_file=output_file,
        deployment_label=deployment_label,
        clipped_keys=tuple(clipped),
        copied_keys=tuple(copied),
        empty_keys=tuple(empty),
    )


def _to_utc_timestamp(value: datetime) -> pd.Timestamp:
    """Coerce a window bound to a UTC timestamp, taking a naive value as UTC.

    Every timestamp in a bundle is ``datetime64[ns, UTC]``, so a naive bound
    has to be given a zone before it can be compared against one at all.
    """
    timestamp: pd.Timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _clipped_deployment_label(
    reader: DeploymentBundleReader, label_suffix: str
) -> str:
    """Read the source deployment's label and join the suffix onto it.

    Every bundle is written onto the identity field names the descriptor
    models use, so the label is read unconditionally rather than probed for.
    """
    if not reader.has_frame(_IDENTITY_KEY):
        raise ValueError(
            f"bundle holds no frame at {_IDENTITY_KEY!r}: "
            f"a clip needs the source deployment's identity"
        )

    identity: pd.DataFrame = reader.read_frame(_IDENTITY_KEY)
    source_label: str = str(identity["deployment_label"].iloc[0])
    return f"{source_label}_{label_suffix}"
