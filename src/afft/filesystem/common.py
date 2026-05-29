"""Module for common filesystem functions."""

import os
import shutil

from pathlib import Path
from typing import Callable, Optional


def list_directory(
    directory: Path,
    filter_fun: Optional[Callable[[Path], bool]] = None,
) -> list[Path]:
    """list file paths in a directory with the possibility to filter.
    filter:
        return true to keep
        return false to discard
    """
    paths: list[Path] = [
        Path(os.path.abspath(os.path.join(directory, filename)))
        for filename in os.listdir(directory)
    ]
    if filter_fun is not None:
        paths = [path for path in paths if filter_fun(path)]
    return paths


def make_directories(directory: Path, exist_ok: bool = False) -> None:
    """Creates the ancestor directories for the given path."""
    os.makedirs(str(directory), exist_ok=exist_ok)


def copy_file(
    source: Path, destination: Path, follow_symlinks: bool = True
) -> Path:
    """Copies a file from the source to the destination."""
    shutil.copyfile(
        str(source), str(destination), follow_symlinks=follow_symlinks
    )
    return destination


def get_path_size(path: Path) -> int:
    """Returns the size for a file path."""
    if not path.exists():
        raise FileNotFoundError(f"path does not exist: {path}")

    return os.path.getsize(str(path))
