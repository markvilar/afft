"""Supporting functions for the common deployment bundle tasks: key
validation, frame reading, and input validation."""

import re

from pathlib import Path

import pandas as pd

from .task_types import IngestBundleFrameCommand

type BundleFrameKey = str

_SEGMENT_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_bundle_frame_key(key: BundleFrameKey) -> None:
    """
    Validate a bundle key's structure.

    The check is deliberately structural only -- the key is not matched
    against the bundle layer layout. ``metocean/<provider>/<variable>`` is
    open-ended by design, so providers and variables cannot be enumerated
    in advance, and ingest stays free of schema knowledge.

    Arguments
    ---------
    key: Bundle key to validate.

    Raises
    ------
    ValueError: If the key is empty, is slash-delimited at either end,
        holds an empty segment, or holds a segment with characters outside
        letters, digits, underscore, dot, and hyphen.
    """
    if not key:
        raise ValueError("frame key is empty")

    if key.startswith("/") or key.endswith("/"):
        raise ValueError(f"frame key has a leading or trailing slash: {key!r}")

    for segment in key.split("/"):
        if not segment:
            raise ValueError(f"frame key has an empty segment: {key!r}")
        if not _SEGMENT_PATTERN.match(segment):
            raise ValueError(
                f"frame key segment {segment!r} holds characters outside "
                f"letters, digits, underscore, dot, and hyphen: {key!r}"
            )


def read_frame_file(
    input_file: Path,
    datetime_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """
    Read a CSV file into a frame, parsing the named columns as timezone-aware
    UTC timestamps.

    Columns outside `datetime_columns` keep the dtype ``read_csv`` inferred.
    The datetime columns are parsed with the same call the bundle readers
    use, so both paths agree on how ISO text becomes a timestamp.

    Arguments
    ---------
    input_file: Path to the CSV file.
    datetime_columns: Columns to parse as timestamps.

    Returns
    -------
    The frame, with each named column cast to ``datetime64[ns, UTC]``.

    Raises
    ------
    ValueError: If a named datetime column is not in the file.
    """
    frame: pd.DataFrame = pd.read_csv(input_file)

    missing: list[str] = [
        column for column in datetime_columns if column not in frame.columns
    ]
    if missing:
        raise ValueError(
            f"datetime columns {missing} are not in {input_file}: "
            f"columns are {list(frame.columns)}"
        )

    for column in datetime_columns:
        frame[column] = pd.to_datetime(
            frame[column], utc=True, format="ISO8601"
        )

    return frame


def validate_ingest_bundle_frame_input(
    command: IngestBundleFrameCommand,
) -> None:
    """
    Validate the task's inputs before any expensive work runs.

    Arguments
    ---------
    command: Task command.

    Raises
    ------
    FileNotFoundError: If the bundle or the input file does not exist.
    ValueError: If the frame key is not structurally valid.
    """
    validate_bundle_frame_key(command.key)

    if not command.bundle_file.is_file():
        raise FileNotFoundError(
            f"deployment bundle does not exist: {command.bundle_file}"
        )

    if not command.input_file.is_file():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
