import glob

from pathlib import Path
from typing import List

from loguru import logger

from result import Ok, Err, Result

def search_directory_tree(search_path: Path) -> Result[List[Path], str]:
    """ Searches a directory tree from the root to find items that match the
    given pattern. """
    matched_files: List[str] = glob.glob(str(search_path), recursive=True)

    if not matched_files:
        return Err(f"no matched file in path: {search_path}")
    else:
        return Ok([Path(path) for path in matched_files])
