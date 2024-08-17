"""Module for writing data to files. Supported formats are JSON, YAML, TOML and msgpack."""

from pathlib import Path

import msgspec

from result import Ok, Err, Result


def write_json(data: dict, path: Path, mode: str="w") -> Result[Path, str]:
    """Writes an object to a JSON file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.json.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def write_yaml(data: dict, path: Path, mode: str="w") -> Result[Path, str]:
    """Writes an object to a YAML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.yaml.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def write_toml(data: dict, path: Path, mode: str="w") -> Result[Path, str]:
    """Writes an object to a TOML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.toml.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def write_msgpack(data: dict, path: Path, mode: str="w") -> Result[Path, str]:
    """Writes an object to a MSGPACK file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.msgpack.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))

