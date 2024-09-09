"""Module for filesystem query types."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileQueryData:
    """Class representing file query data."""

    pattern: str
    recursive: bool


@dataclass
class FileSelection:
    """Class representing a file selection."""

    files: list[Path]
