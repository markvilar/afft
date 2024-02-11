""" Common filesystem functions. """
import os

from pathlib import Path
from typing import List

from result import Ok, Err, Result

def get_path_size(path: Path) -> Result[int, str]:
    """ Returns the size for a file path. Assumes that the path exists. """
    if not path.exists():
        return Err(f"path does not exist: {path}")

    size = os.path.getsize(str(path))
    return Ok(size)

def get_largest_file(paths: List[Path]) -> Path:
    """ Returns the path of largest file. """
    sizes = dict([ (path, get_path_size(path).unwrap()) for path in paths])
    current_path, current_size = Path(""), 0
    for path in sizes:
        if sizes[path] > current_size:
            current_path = path
            current_size = sizes[path]
    return current_path
