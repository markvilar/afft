"""Tests for configuration file IO across all supported formats."""

from pathlib import Path
from typing import Any

import msgspec
import pytest

from afft.io import read_config, write_config

# Values common to every format: no ``None`` (unsupported by TOML), a mix of
# scalar types, a list, and a nested table.
SAMPLE_DATA: dict[str, Any] = {
    "name": "SEABED",
    "count": 3,
    "ratio": 0.5,
    "enabled": True,
    "streams": ["RAW", "MSG", "CTL"],
    "nested": {"depth": 10, "label": "inner"},
}

# Text-based formats whose on-disk bytes are valid UTF-8 text.
TEXT_SUFFIXES: list[str] = [".json", ".yaml", ".yml", ".toml"]

# All formats, including the binary msgpack representation.
ALL_SUFFIXES: list[str] = TEXT_SUFFIXES + [".msgpack"]


@pytest.mark.parametrize("suffix", ALL_SUFFIXES)
def test_write_then_read_round_trips(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"config{suffix}"

    write_config(SAMPLE_DATA, path)
    restored = read_config(path)

    assert restored == SAMPLE_DATA


@pytest.mark.parametrize("suffix", ALL_SUFFIXES)
def test_write_config_returns_path(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"config{suffix}"

    assert write_config(SAMPLE_DATA, path) == path


@pytest.mark.parametrize("suffix", TEXT_SUFFIXES)
def test_text_formats_are_written_as_utf8_text(
    tmp_path: Path, suffix: str
) -> None:
    path = tmp_path / f"config{suffix}"
    write_config(SAMPLE_DATA, path)

    # A text format decodes cleanly as UTF-8 and mentions the string values.
    text = path.read_text(encoding="utf-8")
    assert "SEABED" in text
    assert "inner" in text


def test_msgpack_is_written_as_binary(tmp_path: Path) -> None:
    path = tmp_path / "config.msgpack"
    write_config(SAMPLE_DATA, path)

    # The raw bytes are exactly the msgpack encoding ...
    assert path.read_bytes() == msgspec.msgpack.encode(SAMPLE_DATA)

    # ... and are genuinely binary: not decodable as UTF-8 text.
    with pytest.raises(UnicodeDecodeError):
        path.read_text(encoding="utf-8")


def test_read_config_unknown_suffix_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.txt"
    path.write_text("nonsense")

    with pytest.raises(NotImplementedError):
        read_config(path)


def test_write_config_unknown_suffix_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.txt"

    with pytest.raises(NotImplementedError):
        write_config(SAMPLE_DATA, path)
