"""Module for reading and writing text files."""

from pathlib import Path


def read_lines(path: Path, mode: str = "r") -> list[str]:
    """Reads lines from a text file."""
    if not path.is_file():
        raise ValueError(f"path {path} is not a file")

    try:
        with open(path, mode) as filehandle:
            lines = filehandle.readlines()
            lines = [line.replace("\n", "") for line in lines]
            return lines
    except Exception as exception:
        raise exception


def write_lines(lines: list[str], path: Path, mode: str = "w") -> Path:
    """Writes lines to a text file."""

    if not path.parent.exists():
        raise ValueError(f"directory does not exist: {path.parent}")

    try:
        with open(path, mode) as filehandle:
            lines = [line + "\n" for line in lines]
            filehandle.writelines(lines)
        return path
    except Exception as exception:
        raise exception
