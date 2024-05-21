"""Module for reading and writing text files."""

from pathlib import Path

from result import Ok, Err, Result


def read_file(path: Path, mode: str = "r") -> Result[list[str], str]:
    """Reads lines from a text file."""
    if not path.is_file():
        return Err(f"path {path} is not a file")

    try:
        with open(path, mode) as filehandle:
            lines = filehandle.readlines()
            lines = [line.replace("\n", "") for line in lines]
            return Ok(lines)
    except IOError as error:
        return Err(f"error when reading from file: {error}")


def write_file(lines: list[str], path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes lines to a text file."""

    if not path.parent.exists():
        return Err(f"directory does not exist: {path.parent}")

    try:
        with open(path, mode) as filehandle:
            lines = [line + "\n" for line in lines]
            filehandle.writelines(lines)
        return Ok(path)
    except IOError as error:
        return Err(f"error when writing to file: {error}")
