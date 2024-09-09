"""Module for group export data types."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileExportContext:
    """Class representing a file export context."""

    data_directory: Path
    metafile: Path
    output_directory: Path
    prefix: str
