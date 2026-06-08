"""Data types for the process renav task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ProcessRenavPosesCommand:
    """
    Command for processing a Renav stereo pose estimate file.

    Attributes
    ----------
    input_file: Path to the Renav `.data` file.
    output_file: Path to write the processed output as CSV.
    """

    input_file: Path
    output_file: Path


@dataclass(slots=True, frozen=True)
class ProcessRenavPosesBatchCommand:
    """
    Command for batch processing Renav stereo pose estimate files.

    Attributes
    ----------
    input_dir: Directory containing Renav pose estimate files.
    output_dir: Directory to write the processed CSV files into.
    pattern: Glob pattern to select input files in ``input_dir``.
    """

    input_dir: Path
    output_dir: Path
    pattern: str = "*.txt"
