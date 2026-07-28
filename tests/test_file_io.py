"""Tests for line-based text file IO."""

from pathlib import Path

import pytest

from afft.io import read_lines, write_lines


def test_write_then_read_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "lines.txt"
    lines = ["first", "second", "third"]

    write_lines(lines, path)

    assert read_lines(path) == lines


def test_write_lines_returns_path(tmp_path: Path) -> None:
    path = tmp_path / "lines.txt"

    assert write_lines(["a"], path) == path


def test_read_lines_strips_newlines(tmp_path: Path) -> None:
    path = tmp_path / "lines.txt"
    path.write_text("alpha\nbeta\ngamma\n")

    assert read_lines(path) == ["alpha", "beta", "gamma"]


def test_read_lines_missing_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "does_not_exist.txt"

    with pytest.raises(ValueError):
        read_lines(path)


def test_write_lines_missing_directory_raises(tmp_path: Path) -> None:
    path = tmp_path / "missing_dir" / "lines.txt"

    with pytest.raises(ValueError):
        write_lines(["a"], path)
