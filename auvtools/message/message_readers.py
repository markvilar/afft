"""Read functions for AUV message lines."""

from pathlib import Path
from typing import List, TypeAlias

from loguru import logger
from result import Ok, Err, Result

from auvtools.io import read_file

Line: TypeAlias = str
Lines: TypeAlias = List[Line]

ReadResult: TypeAlias = Result[Lines, str]


def read_message_lines(filepath: Path) -> ReadResult:
    """Reads message lines from an AUV raw file."""
    if not filepath.suffix == ".auv":
        return Err(f"invalid message file extension: {filepath}")
    if not filepath.name.endswith(".RAW.auv"):
        return Err(f"invalid message file type: {filepath}")

    return read_file(filepath)
