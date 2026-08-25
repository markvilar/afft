"""TOML round-trip IO for the parsed SEABED system config structure."""

from pathlib import Path

from afft.io import read_config, write_config

from .system_types import SeabedSystemConfig


def read_system_config(path: Path) -> SeabedSystemConfig:
    """
    Reads a SeabedSystemConfig from our TOML representation.

    Inverse of ``write_system_config``. Purely IO — no vendor-format logic.

    Arguments
    ---------
    path: Path to a TOML file written by ``write_system_config``.

    Returns
    -------
    The parsed SeabedSystemConfig.
    """
    return SeabedSystemConfig.model_validate(read_config(path))


def write_system_config(path: Path, config: SeabedSystemConfig) -> None:
    """
    Writes a SeabedSystemConfig to our TOML representation.

    Purely IO — no vendor-format logic.

    Arguments
    ---------
    path: Destination TOML file path.
    config: The system config to persist.
    """
    write_config(config.model_dump(), path)
