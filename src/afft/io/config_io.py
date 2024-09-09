"""Module for reading and writing data from configuration files. Supported formats are JSON, 
YAML, TOML and msgpack."""

from pathlib import Path

import msgspec

from ..utils.result import Ok, Err, Result


def read_config(path: Path, mode: str = "r") -> Result[dict, str]:
    """Reads data from a configuration file."""

    match path.suffix:
        case ".json":
            return _read_json(path, mode)
        case ".yaml" | ".yml":
            return _read_yaml(path, mode)
        case ".toml":
            return _read_toml(path, mode)
        case ".msgpack":
            return _read_msgpack(path, mode)
        case _:
            raise NotImplementedError(f"invalid config file format: {path}")


def write_config(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes data to a configuration file."""

    match path.suffix:
        case ".json":
            return _write_json(data, path, mode)
        case ".yaml" | ".yml":
            return _write_yaml(data, path, mode)
        case ".toml":
            return _write_toml(data, path, mode)
        case ".msgpack":
            return _write_msgpack(data, path, mode)
        case _:
            raise NotImplementedError(f"invalid config file format: {path}")


def _read_json(path: Path, mode: str = "r") -> Result[dict, str]:
    """Reads data from a JSON file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.json.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def _read_yaml(path: Path, mode: str = "r") -> Result[dict, str]:
    """Reads data from a YAML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.yaml.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def _read_toml(path: Path, mode: str = "r") -> Result[dict, str]:
    """Reads data from a TOML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.toml.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def _read_msgpack(path: Path, mode: str = "r") -> Result[dict, str]:
    """Reads data from a MSGPACK file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict = msgspec.msgpack.decode(handle.read())
            return Ok(data)
    except IOError as error:
        return Err(str(error))


def _write_json(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes an object to a JSON file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.json.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def _write_yaml(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes an object to a YAML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.yaml.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def _write_toml(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes an object to a TOML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.toml.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))


def _write_msgpack(data: dict, path: Path, mode: str = "w") -> Result[Path, str]:
    """Writes an object to a MSGPACK file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.msgpack.encode(data))
            return Ok(path)
    except IOError as error:
        return Err(str(error))
