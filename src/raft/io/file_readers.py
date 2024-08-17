"""Module for reading data from files. Supported formats are JSON, YAML, TOML and msgpack."""

from pathlib import Path

import msgspec

from result import Ok, Err, Result


def read_json(path: Path, mode: str="r") -> Result[dict, str]:
    """Reads data from a JSON file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.json.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def read_yaml(path: Path, mode: str="r") -> Result[dict, str]:
    """Reads data from a YAML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.yaml.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def read_toml(path: Path, mode: str="r") -> Result[dict, str]:
    """Reads data from a TOML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.toml.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def read_msgpack(path: Path, mode: str="r") -> Result[dict, str]:
    """Reads data from a MSGPACK file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.msgpack.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


