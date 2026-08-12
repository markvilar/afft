"""Data types for the common deployment bundle tasks."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class IngestBundleFrameCommand(BaseModel):
    """
    Attributes
    ----------
    bundle_file: Path to the deployment bundle to ingest into. Written in
        place; it must already exist.
    key: Bundle key to write the frame to.
    input_file: Path to the CSV file holding the frame.
    datetime_columns: Columns to parse as timezone-aware UTC timestamps.
        Every other column keeps the dtype ``read_csv`` inferred.
    overwrite: Overwrite an existing frame at ``key``.
    """

    model_config = ConfigDict(frozen=True)

    bundle_file: Path
    key: str
    input_file: Path
    datetime_columns: tuple[str, ...] = ()
    overwrite: bool = False


class ExportBundleFrameCommand(BaseModel):
    """
    Attributes
    ----------
    bundle_file: Path to the deployment bundle to export from. Read only;
        never written.
    key: Bundle key to read the frame from.
    output_file: Path to write the frame to. Its suffix selects the output
        format.
    overwrite: Overwrite an existing output file.
    """

    model_config = ConfigDict(frozen=True)

    bundle_file: Path
    key: str
    output_file: Path
    overwrite: bool = False


class ClipDeploymentBundleCommand(BaseModel):
    """
    Attributes
    ----------
    input_file: Path to the deployment bundle to clip. Read only; never
        written.
    output_file: Path to write the clipped bundle to.
    start: Start of the clip window, inclusive.
    end: End of the clip window, inclusive.
    label_suffix: Appended to the source deployment label, joined with an
        underscore, to name the clipped deployment.
    datetime_column: Column to clip on. Frames without it are copied whole.
    no_clip_patterns: Key patterns whose frames are copied whole even if they
        carry ``datetime_column``.
    overwrite: Overwrite an existing output file.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    output_file: Path
    start: datetime
    end: datetime
    label_suffix: str
    datetime_column: str = "timestamp"
    no_clip_patterns: tuple[str, ...] = ()
    overwrite: bool = False


class ClippedFrame(BaseModel):
    """
    Attributes
    ----------
    key: Bundle key of the frame that was clipped.
    rows_before: Row count in the source frame.
    rows_after: Row count inside the clip window.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    rows_before: int
    rows_after: int


class IngestBundleFrameResult(BaseModel):
    """
    Attributes
    ----------
    bundle_file: Path to the bundle the frame was written to.
    key: Bundle key the frame was written to.
    rows: Number of rows written.
    columns: Column names written, in frame order.
    """

    model_config = ConfigDict(frozen=True)

    bundle_file: Path
    key: str
    rows: int
    columns: tuple[str, ...]


class ExportBundleFrameResult(BaseModel):
    """
    Attributes
    ----------
    output_file: Path the frame was written to.
    key: Bundle key the frame was read from.
    rows: Number of rows written.
    columns: Column names written, in frame order.
    """

    model_config = ConfigDict(frozen=True)

    output_file: Path
    key: str
    rows: int
    columns: tuple[str, ...]


class ClipDeploymentBundleResult(BaseModel):
    """
    Attributes
    ----------
    input_file: Path to the bundle that was clipped.
    output_file: Path the clipped bundle was written to.
    deployment_label: Label of the clipped deployment.
    clipped_keys: Keys whose frames were clipped, with their row counts before
        and after.
    copied_keys: Keys whose frames were copied whole.
    empty_keys: Keys the window clipped to zero rows. Reported separately
        rather than read off ``clipped_keys``, since it is the field a caller
        checks to find out whether the window was wrong.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    output_file: Path
    deployment_label: str
    clipped_keys: tuple[ClippedFrame, ...]
    copied_keys: tuple[str, ...]
    empty_keys: tuple[str, ...]
