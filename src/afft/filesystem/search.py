"""Module for filesystem search functionality."""

from glob import glob
from pathlib import Path


def search_directory_tree(search_path: Path) -> list[Path]:
    """Searches a directory tree from the root to find items that match the
    given pattern."""
    matched_files: list[str] = glob(str(search_path), recursive=True)

    if not matched_files:
        raise FileNotFoundError(f"no matched file in path: {search_path}")

    return [Path(path) for path in matched_files]


def search_directory(
    path: Path, pattern: str, recursive: bool = False
) -> list[Path]:
    """Searches a directory for filesystem items matching the given pattern."""
    if not path.exists():
        raise FileNotFoundError(f"path does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"path is not a directory: {path}")

    matches: list[str] = glob(str(path / pattern), recursive=recursive)
    return [Path(match) for match in matches]
