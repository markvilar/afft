"""Data types for the common deployment bundle tasks."""

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
