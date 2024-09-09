"""Module with data types for the file descriptor generation."""

from dataclasses import dataclass
from pathlib import Path

from ...filesystem import FileQueryData


@dataclass
class QueryItem:
    """Class representing a query item."""

    name: str
    directory: Path
    query_data: FileQueryData


@dataclass
class SelectionItem:
    """Class representing a selection item."""

    name: str
    files: list[Path]


@dataclass
class MetafileGenerationContext:
    """Class representing a metafile generation context."""

    root_directory: Path
    output_directory: Path
    prefix: str
