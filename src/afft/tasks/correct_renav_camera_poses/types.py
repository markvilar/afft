"""Data types for the correct renav camera poses task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class CorrectRenavCameraPosesResult:
    """
    Result of correcting Renav camera poses for a single deployment.

    Attributes
    ----------
    total: Total number of rows in the target frame.
    matched: Rows with a direct match in the source frame.
    unmatched: Rows with no source match (NaN before interpolation).
    interpolated: Unmatched rows filled by linear interpolation.
    remaining_nan: Rows still NaN after interpolation (leading/trailing edge).
    """

    total: int
    matched: int
    unmatched: int
    interpolated: int
    remaining_nan: int


@dataclass(slots=True, frozen=True)
class CorrectRenavCameraPosesBatchResult:
    """
    Diagnostics from batch-correcting Renav camera poses across deployments.

    Attributes
    ----------
    results: Per-deployment correction statistics, keyed by deployment label.
    skipped: Deployment labels for which no matching source file was found.
    """

    results: dict[str, CorrectRenavCameraPosesResult]
    skipped: list[str]


@dataclass(slots=True, frozen=True)
class CorrectRenavCameraPosesConfig:
    """
    Column configuration for the correct renav camera poses task.

    Attributes
    ----------
    target_join_column: Column in the target frame used as the join key.
    target_latitude_column: Latitude column in the target frame to replace.
    target_longitude_column: Longitude column in the target frame to replace.
    source_join_column: Column in the source frame used as the join key.
    source_latitude_column: Latitude column in the source frame.
    source_longitude_column: Longitude column in the source frame.
    """

    target_join_column: str = "stereo_left_label"
    target_latitude_column: str = "latitude"
    target_longitude_column: str = "longitude"
    source_join_column: str = "key"
    source_latitude_column: str = "pose.lat"
    source_longitude_column: str = "pose.lon"


@dataclass(slots=True, frozen=True)
class CorrectRenavCameraPosesCommand:
    """
    Command for correcting Renav camera poses with source camera poses.

    Attributes
    ----------
    target_file: Path to the target camera pose CSV (e.g. processed Renav).
    source_file: Path to the source camera pose CSV (e.g. Squidle+).
    output_file: Path to write the corrected output as CSV.
    """

    target_file: Path
    source_file: Path
    output_file: Path


@dataclass(slots=True, frozen=True)
class CorrectRenavCameraPosesBatchCommand:
    """
    Command for batch-correcting Renav camera poses with source camera poses.

    Attributes
    ----------
    target_dir: Directory containing target camera pose CSV files.
    source_dir: Directory containing source camera pose CSV files.
    output_dir: Directory to write the corrected CSV files into.
    target_suffix: Suffix stripped from target filenames to derive the
        deployment label (e.g. ``"_renav_stereo_poses.csv"``).
    source_suffix: Suffix appended to the deployment label to find the
        matching source file (e.g. ``"_cameras.csv"``).
    """

    target_dir: Path
    source_dir: Path
    output_dir: Path
    target_suffix: str = "_renav_stereo_poses.csv"
    source_suffix: str = "_cameras.csv"
