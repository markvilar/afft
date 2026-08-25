"""TOML round-trip IO for the parsed SEABED localizer config structure."""

from pathlib import Path

from afft.io import read_config, write_config

from .localizer_types import SeabedLocalizerConfig


def read_localizer_config(path: Path) -> SeabedLocalizerConfig:
    """
    Reads a SeabedLocalizerConfig from our TOML representation.

    Inverse of ``write_localizer_config``. Purely IO — no vendor-format logic.

    Arguments
    ---------
    path: Path to a TOML file written by ``write_localizer_config``.

    Returns
    -------
    The parsed SeabedLocalizerConfig.
    """
    return SeabedLocalizerConfig.model_validate(read_config(path))


def write_localizer_config(path: Path, config: SeabedLocalizerConfig) -> None:
    """
    Writes a SeabedLocalizerConfig to our TOML representation.

    Purely IO — no vendor-format logic.

    Arguments
    ---------
    path: Destination TOML file path.
    config: The localizer config to persist.
    """
    write_config(config.model_dump(), path)
