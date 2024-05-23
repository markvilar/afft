"""Module for common filesystem functions."""

import os

from pathlib import Path
from typing import Callable

from loguru import logger
from result import Ok, Err, Result


def list_directory(
    directory: Path,
    filter_fun: Callable[[Path], bool] = None,
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
    if filter_fun:
        paths: list[Path] = [path for path in paths if filter_fun(path)]
    return paths


def make_directories(directory: Path, exist_ok: bool = False) -> None:
    """Creates the ancestor directories for the given path."""
    os.makedirs(str(directory), exist_ok=exist_ok)


def get_path_size(path: Path) -> Result[int, str]:
    """Returns the size for a file path. Assumes that the path exists."""
    if not path.exists():
        return Err(f"path does not exist: {path}")

    size: int = os.path.getsize(str(path))
    return Ok(size)


def get_largest_file(paths: list[Path]) -> Path:
    """Returns the path of largest file."""
    sizes = dict([(path, get_path_size(path).unwrap()) for path in paths])
    current_path, current_size = Path(""), 0
    for path in sizes:
        if sizes[path] > current_size:
            current_path = path
            current_size = sizes[path]
    return current_path


def sort_paths_by_filename(
    unsorted_paths: list[Path], key_fun: Callable[[Path], str] = lambda path: path.name
) -> list[Path]:
    """Sorts paths by their keys. The default path key is the file name.

    Arguments:
    - unsorted_paths: unsorted list of paths
    - key_fun: function that returns the key for a path

    Returns:
    - sorted list of paths
    """
    return sorted(unsorted_paths, key=key_fun)
