"""Supporting functions for the common deployment bundle tasks: key
validation, frame reading and writing, and input validation."""

import fnmatch
import re

from collections.abc import Callable
from pathlib import Path

import geopandas as gpd
import pandas as pd

from .task_types import (
    ClipDeploymentBundleCommand,
    ExportBundleFrameCommand,
    IngestBundleFrameCommand,
)

type BundleFrameKey = str
type FrameWriter = Callable[[pd.DataFrame, Path], None]
type GeoFrameWriter = Callable[[gpd.GeoDataFrame, Path], None]

_SEGMENT_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9._-]+$")

_GEOFRAME_SUFFIXES: frozenset[str] = frozenset({".geojson", ".gpkg"})


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


def _parse_datetime_columns(
    frame: pd.DataFrame, input_file: Path, datetime_columns: tuple[str, ...]
) -> None:
    """
    Parse `datetime_columns` of `frame` in place as timezone-aware UTC
    timestamps.

    Arguments
    ---------
    frame: Frame to parse columns of, mutated in place.
    input_file: Path `frame` was read from, named in any error.
    datetime_columns: Columns to parse as timestamps.

    Raises
    ------
    ValueError: If a named datetime column is not in `frame`.
    """
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


def read_frame_file(
    input_file: Path,
    datetime_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """
    Read a CSV file into a frame, parsing the named columns as timezone-aware
    UTC timestamps.

    Columns outside `datetime_columns` keep the dtype ``read_csv`` inferred.

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
    _parse_datetime_columns(frame, input_file, datetime_columns)
    return frame


def is_geoframe_suffix(suffix: str) -> bool:
    """Whether `suffix` names a geodata file format."""
    return suffix in _GEOFRAME_SUFFIXES


def read_geoframe_file(
    input_file: Path,
    datetime_columns: tuple[str, ...] = (),
) -> gpd.GeoDataFrame:
    """
    Read a geodata file into a geoframe, parsing the named columns as
    timezone-aware UTC timestamps.

    The source CRS is passed through as-is -- no reprojection, no
    validation against a specific CRS. `write_geoframe` is the one place
    that enforces a CRS must be set at all.

    ``DATE_AS_STRING`` disables the reader's own datetime auto-detection, so
    every datetime-like field comes back as its original source text rather
    than GDAL's parsed representation. GDAL's parser has a rounding bug that
    corrupts a value with more than millisecond precision (e.g. rounding
    ``59.999526024`` seconds up to an invalid ``60`` seconds) and silently
    downgrades the whole column to mangled strings; reading as text and
    parsing `datetime_columns` with pandas instead sidesteps that entirely.
    Datetime-like fields outside `datetime_columns` are left as plain text
    rather than auto-parsed, matching `read_frame_file`'s CSV behaviour.

    Arguments
    ---------
    input_file: Path to the geodata file.
    datetime_columns: Columns to parse as timestamps.

    Returns
    -------
    The geoframe, with its geometry column and CRS as read from the file.

    Raises
    ------
    ValueError: If a named datetime column is not in the file.
    """
    geoframe: gpd.GeoDataFrame = gpd.read_file(input_file, DATE_AS_STRING="YES")
    _parse_datetime_columns(geoframe, input_file, datetime_columns)
    return geoframe


def write_frame_file(frame: pd.DataFrame, output_file: Path) -> None:
    """
    Write a frame to a file, choosing the writer from the file's suffix.

    The index is not written where the writer offers the choice. Bundle
    frames carry a default ``RangeIndex``, so an index column would be a
    row number that the reader would then take for data.

    Arguments
    ---------
    frame: Frame to write.
    output_file: Path to write to. Its suffix selects the writer.

    Raises
    ------
    ValueError: If the suffix does not name a supported format.
    """
    writer: FrameWriter | None = _FRAME_WRITERS.get(output_file.suffix)
    if writer is None:
        raise ValueError(
            f"unsupported output file suffix {output_file.suffix!r}: "
            f"{output_file}; supported suffixes are "
            f"{sorted(_FRAME_WRITERS)}"
        )

    writer(frame, output_file)


def write_geoframe_file(frame: gpd.GeoDataFrame, output_file: Path) -> None:
    """
    Write a geoframe to a geodata file, choosing the driver from the file's
    suffix.

    Arguments
    ---------
    frame: Geoframe to write.
    output_file: Path to write to. Its suffix selects the driver.

    Raises
    ------
    ValueError: If the suffix does not name a supported geodata format.
    """
    if not is_geoframe_suffix(output_file.suffix):
        raise ValueError(
            f"unsupported geodata output file suffix "
            f"{output_file.suffix!r}: {output_file}; supported suffixes "
            f"are {sorted(_GEOFRAME_SUFFIXES)}"
        )

    frame.to_file(output_file)


def validate_export_bundle_frame_input(
    command: ExportBundleFrameCommand,
) -> None:
    """
    Validate the task's inputs before the bundle is opened.

    Whether the key holds a frame is not checked here -- that needs the
    bundle open, and the runner reports it against the keys the bundle
    actually holds.

    Arguments
    ---------
    command: Task command.

    Raises
    ------
    FileNotFoundError: If the bundle does not exist.
    FileExistsError: If the output file exists and ``overwrite`` is not set.
    ValueError: If the frame key is not structurally valid, or if the
        output file's suffix does not name a supported format.
    """
    validate_bundle_frame_key(command.key)

    if (
        command.output_file.suffix not in _FRAME_WRITERS
        and not is_geoframe_suffix(command.output_file.suffix)
    ):
        raise ValueError(
            f"unsupported output file suffix "
            f"{command.output_file.suffix!r}: {command.output_file}; "
            f"supported suffixes are "
            f"{sorted(set(_FRAME_WRITERS) | _GEOFRAME_SUFFIXES)}"
        )

    if not command.bundle_file.is_file():
        raise FileNotFoundError(
            f"deployment bundle does not exist: {command.bundle_file}"
        )

    if command.output_file.exists() and not command.overwrite:
        raise FileExistsError(
            f"output file already exists: {command.output_file}: "
            f"pass overwrite to replace it"
        )


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


def key_matches_no_clip(key: BundleFrameKey, patterns: tuple[str, ...]) -> bool:
    """
    Whether a key matches any of the no-clip patterns.

    Patterns are `fnmatch` globs matched against the whole key. ``*`` crosses
    slash boundaries there, so ``metocean/*`` matches
    ``metocean/stormglass/wave_height`` as intended.

    Arguments
    ---------
    key: Bundle key to test.
    patterns: Key patterns whose frames are copied whole.

    Returns
    -------
    Whether the frame at `key` should keep every row.
    """
    return any(fnmatch.fnmatch(key, pattern) for pattern in patterns)


def clip_frame_to_window(
    key: BundleFrameKey,
    frame: pd.DataFrame,
    datetime_column: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """
    Clip a frame's rows to a closed window on its datetime column.

    The window is ``start <= t <= end``, so a range quoted as covering both
    of its bounds keeps the rows sitting on them. Consecutive windows sharing
    a bound therefore both keep the row on it -- cutting a source into
    adjacent clips duplicates that row rather than partitioning cleanly.

    The result is taken by boolean mask rather than rebuilt, which is what
    keeps a window matching no rows an empty frame with the source's dtypes
    intact rather than an empty frame of objects.

    Arguments
    ---------
    key: Bundle key the frame was read from, named in any error.
    frame: Frame to clip; not mutated.
    datetime_column: Column to clip on.
    start: Start of the window, inclusive.
    end: End of the window, inclusive.

    Returns
    -------
    The rows of `frame` inside the window.

    Raises
    ------
    ValueError: If `datetime_column` is not a datetime column. A frame
        carrying the name on a non-temporal column cannot be clipped, and
        copying it whole instead would silently keep rows outside the window.
    """
    column: pd.Series = frame[datetime_column]
    if not pd.api.types.is_datetime64_any_dtype(column):
        raise ValueError(
            f"{key}: column {datetime_column!r} is not a datetime column, "
            f"got {column.dtype}"
        )

    return frame[(column >= start) & (column <= end)].reset_index(drop=True)


def validate_clip_deployment_bundle_input(
    command: ClipDeploymentBundleCommand,
) -> None:
    """
    Validate the task's inputs before the bundle is opened.

    Arguments
    ---------
    command: Task command.

    Raises
    ------
    FileNotFoundError: If the input bundle does not exist.
    ValueError: If the output file is the input file, if it exists and
        ``overwrite`` is not set, if ``start`` is not before ``end``, or if
        ``label_suffix`` is empty.
    """
    if not command.label_suffix:
        raise ValueError("label suffix is empty")

    if command.start >= command.end:
        raise ValueError(
            f"clip window start must be before its end: "
            f"{command.start.isoformat()} >= {command.end.isoformat()}"
        )

    if not command.input_file.is_file():
        raise FileNotFoundError(
            f"deployment bundle does not exist: {command.input_file}"
        )

    if command.output_file == command.input_file:
        raise ValueError(
            f"output file is the input bundle: {command.output_file}; "
            f"a clip is written to a new bundle"
        )

    if command.output_file.exists() and not command.overwrite:
        raise ValueError(
            f"output file already exists: {command.output_file}: "
            f"pass overwrite to replace it"
        )


def _write_csv(frame: pd.DataFrame, output_file: Path) -> None:
    """Write a frame as CSV, with timestamps as ISO8601 in UTC.

    The default timestamp rendering is what ``read_frame_file`` parses back
    with ``format="ISO8601"``, which is what keeps an exported CSV
    ingestable.
    """
    frame.to_csv(output_file, index=False)


def _write_parquet(frame: pd.DataFrame, output_file: Path) -> None:
    frame.to_parquet(output_file, index=False)


def _write_feather(frame: pd.DataFrame, output_file: Path) -> None:
    frame.to_feather(output_file)


def _write_json(frame: pd.DataFrame, output_file: Path) -> None:
    """Write a frame as a JSON array of row objects.

    ``orient="records"`` drops the index, and ``date_format="iso"`` keeps
    timestamps readable rather than rendering them as epoch milliseconds.
    """
    frame.to_json(output_file, orient="records", date_format="iso")


_FRAME_WRITERS: dict[str, FrameWriter] = {
    ".csv": _write_csv,
    ".feather": _write_feather,
    ".json": _write_json,
    ".parquet": _write_parquet,
}
