"""Module for reading TOML files."""

from pathlib import Path
from typing import Dict

import toml

from result import Ok, Err, Result


def read_toml(filepath: Path, mode: str = "r") -> Result[Dict, str]:
    """Reads a toml file and returns the contents as a dictionary."""
    if not filepath.exists():
        return Err(f"path does not exist: {filepath}")
    if not filepath.suffix == ".toml":
        return Err(f"path is not a TOML file: {filepath}")

    try:
        with open(filepath, mode) as filehandle:
            data = toml.load(filehandle)
            return Ok(data)
    except IOError as error:
        return Err(str(error))

    return Err(f"unable to read file: {filepath}")
