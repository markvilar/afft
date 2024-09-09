"""Module for filesystem search functionality."""

from glob import glob
from pathlib import Path

from ..utils.result import Ok, Err, Result


def search_directory_tree(search_path: Path) -> Result[list[Path], str]:
    """Searches a directory tree from the root to find items that match the
    given pattern."""
    matched_files: list[str] = glob(str(search_path), recursive=True)

    if not matched_files:
        return Err(f"no matched file in path: {search_path}")
    else:
        return Ok([Path(path) for path in matched_files])


def search_directory(
    path: Path, pattern: str, recursive: bool = False
) -> Result[list[Path], str]:
    """Searches a directory for filesystem items matching the given pattern."""
    if not path.exists():
        return Err(f"path does not exist: {path}")
    if not path.is_dir():
        return Err(f"path is not a directory: {path}")

    matches: list[str] = glob(str(path / pattern), recursive=recursive)
    return Ok([Path(match) for match in matches])
