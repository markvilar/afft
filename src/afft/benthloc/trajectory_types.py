"""Data types for the Benthloc trajectory ingestion file builder."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class BuildTrajectoryIngestionFileCommand(BaseModel):
    """
    Attributes
    ----------
    bundle_file: Path to the processed deployment bundle to read from, never
        written.
    key: Bundle key of the trajectory geoframe to read.
    output_file: Path to write the Benthloc trajectory ingestion file to.
    trajectory_label: Trajectory label, single-valued across the output
        file.
    trajectory_description: Optional trajectory description.
    timestamp_column: Datetime column on the source geoframe.
    yaw_column: Yaw (heading) column on the source geoframe, degrees.
    pitch_column: Pitch column on the source geoframe, degrees.
    roll_column: Roll column on the source geoframe, degrees.
    platform_label: Platform label override; falls back to the bundle's
        ``platform/identity`` when unset.
    deployment_label: Deployment label override; falls back to the bundle's
        ``deployment/identity`` when unset.
    overwrite: Overwrite `output_file` if it already exists.
    dry_run: Validate and report the labels and pose count without writing.
    """

    model_config = ConfigDict(frozen=True)

    bundle_file: Path
    key: str
    output_file: Path
    trajectory_label: str
    trajectory_description: str | None = None
    timestamp_column: str = "timestamp"
    yaw_column: str = "yaw"
    pitch_column: str = "pitch"
    roll_column: str = "roll"
    platform_label: str | None = None
    deployment_label: str | None = None
    overwrite: bool = False
    dry_run: bool = False


class BuildTrajectoryIngestionFileResult(BaseModel):
    """
    Attributes
    ----------
    output_file: Path the ingestion file was (or would be) written to.
    platform_label: Resolved platform label.
    deployment_label: Resolved deployment label.
    trajectory_label: Trajectory label the file asserts.
    pose_count: Number of poses in the output file.
    dropped_row_count: Rows dropped for a null position, attitude, or
        timestamp.
    start_timestamp: Earliest timestamp in the output file.
    end_timestamp: Latest timestamp in the output file.
    written: Whether the file was actually written (`False` for `dry_run`).
    """

    model_config = ConfigDict(frozen=True)

    output_file: Path
    platform_label: str
    deployment_label: str
    trajectory_label: str
    pose_count: int
    dropped_row_count: int
    start_timestamp: datetime
    end_timestamp: datetime
    written: bool
