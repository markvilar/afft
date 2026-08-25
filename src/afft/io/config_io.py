"""Module for reading and writing data from configuration files. Supported formats are JSON,
YAML, TOML and msgpack."""

from pathlib import Path
from typing import Any

import msgspec


def read_config(path: Path) -> dict[str, Any]:
    """Reads data from a configuration file."""

    match path.suffix:
        case ".json":
            return _read_json(path)
        case ".yaml" | ".yml":
            return _read_yaml(path)
        case ".toml":
            return _read_toml(path)
        case ".msgpack":
            return _read_msgpack(path)
        case _:
            raise NotImplementedError(f"invalid config file format: {path}")


def write_config(data: dict[str, Any], path: Path) -> Path:
    """Writes data to a configuration file."""

    match path.suffix:
        case ".json":
            return _write_json(data, path)
        case ".yaml" | ".yml":
            return _write_yaml(data, path)
        case ".toml":
            return _write_toml(data, path)
        case ".msgpack":
            return _write_msgpack(data, path)
        case _:
            raise NotImplementedError(f"invalid config file format: {path}")


def _read_json(path: Path, mode: str = "r") -> dict[str, Any]:
    """Reads data from a JSON file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict[str, Any] = msgspec.json.decode(handle.read())
            return data
    except Exception as exception:
        raise exception


def _read_yaml(path: Path, mode: str = "r") -> dict[str, Any]:
    """Reads data from a YAML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict[str, Any] = msgspec.yaml.decode(handle.read())
            return data
    except Exception as exception:
        raise exception


def _read_toml(path: Path, mode: str = "r") -> dict[str, Any]:
    """Reads data from a TOML file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict[str, Any] = msgspec.toml.decode(handle.read())
            return data
    except Exception as exception:
        raise exception


def _read_msgpack(path: Path, mode: str = "rb") -> dict[str, Any]:
    """Reads data from a MSGPACK file."""
    try:
        with open(path, mode=mode) as handle:
            data: dict[str, Any] = msgspec.msgpack.decode(handle.read())
            return data
    except Exception as exception:
        raise exception


def _write_json(data: dict[str, Any], path: Path, mode: str = "wb") -> Path:
    """Writes an object to a JSON file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.json.encode(data))
            return path
    except Exception as exception:
        raise exception


def _write_yaml(data: dict[str, Any], path: Path, mode: str = "wb") -> Path:
    """Writes an object to a YAML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.yaml.encode(data))
            return path
    except Exception as exception:
        raise exception


def _write_toml(data: dict[str, Any], path: Path, mode: str = "wb") -> Path:
    """Writes an object to a TOML file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.toml.encode(data))
            return path
    except Exception as exception:
        raise exception


def _write_msgpack(data: dict[str, Any], path: Path, mode: str = "wb") -> Path:
    """Writes an object to a MSGPACK file."""
    try:
        with open(path, mode) as handle:
            handle.write(msgspec.msgpack.encode(data))
            return path
    except Exception as exception:
        raise exception
