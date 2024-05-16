"""Module for reading and writing JSON files."""
import json

from pathlib import Path

from result import Ok, Err, Result


def read_json(filepath: Path) -> Result[dict, str]:
    """Reads a JSON file and returns the content as a dictionary."""
    if not filepath.exists():
        return Err(f"path does not exist: {filepath}")

    try:
        with open(filepath, mode="r") as file_handle:
            data = json.load(file_handle)
        return Ok(data)
    except BaseException as error:
        return Err(str(error))


def write_json(data: dict, filepath: Path) -> Result[Path, str]:
    """Writes a dictionary to a JSON file."""
    if not filepath.parent.exists():
        return Err(f"directory does not exist: {filepath.parent}")

    try:
        serialized = json.dumps(data, indent=4)
        with open(filepath, "w") as filehandle:
            filehandle.write(serialized)
        return Ok(filepath)
    except BaseException as error:
        return Err(str(error))
