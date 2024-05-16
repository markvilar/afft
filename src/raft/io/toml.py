"""Module for reading and writing TOML files."""

from pathlib import Path

import toml

from result import Ok, Err, Result


def read_toml(filepath: Path, mode: str = "r") -> Result[dict, str]:
    """Reads a TOML file and returns the contents as a dictionary."""
    if not filepath.exists():
        return Err(f"path does not exist: {filepath}")
    if not filepath.suffix == ".toml":
        return Err(f"path is not a TOML file: {filepath}")

    try:
        with open(filepath, mode) as file_handle:
            data = toml.load(file_handle)
            return Ok(data)
    except IOError as error:
        return Err(str(error))

    return Err(f"unable to read file: {filepath}")


def write_toml(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Write a dictionary to a TOML file."""
    if not path.parent.exists():
        return Err(f"directory does not exist: {path.parent}")
    if not path.suffix == ".toml":
        return Err(f"invalid TOML extension: {path}")

    try:
        with open(path, mode) as file_handle:
            toml.dump(data, file_handle)
            return Ok(path)
    except IOError as error:
        return Err(str(error))

    return Err(f"unable to write file: {path}")
