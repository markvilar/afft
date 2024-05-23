"""Module for filesystem query types."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileQueryData:
    """Class representing file query data."""

    name: str
    directory: Path
    pattern: str
    recursive: bool


@dataclass
class FileSelection:
    """Class representing a file selection."""

    name: str
    files: list[Path]
