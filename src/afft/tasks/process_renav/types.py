"""Data types for the process renav task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ProcessRenavCommand:
    """
    Command for processing a Renav stereo pose estimate file.

    Attributes
    ----------
    input_file: Path to the Renav `.data` file.
    output_file: Path to write the processed output as CSV.
    """

    input_file: Path
    output_file: Path
