"""Module for common filesystem functions."""

import os
import shutil

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


def copy_file(
    source: Path, destination: Path, follow_symlinks: bool = True
) -> Result[Path, str]:
    """Copies a file from the source to the destination."""
    try:
        shutil.copyfile(str(source), str(destination), follow_symlinks=follow_symlinks)
    except shutil.SameFileError as error:
        return Err(str(error))
    except OSError as error:
        return Err(str(error))

    return Ok(destination)


def get_path_size(path: Path) -> Result[int, str]:
    """Returns the size for a file path. Assumes that the path exists."""
    if not path.exists():
        return Err(f"path does not exist: {path}")

    size: int = os.path.getsize(str(path))
    return Ok(size)
