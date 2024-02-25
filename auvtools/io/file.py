from pathlib import Path
from typing import List

from result import Ok, Err, Result

FileLines = List[str]

def read_file(path: Path, mode: str="r") -> Result[FileLines, str]:
    """ Reads lines from a file. """
    if not path.is_file():
        return Err(f"path {path} is not a file")

    try:
        with open(path, mode) as filehandle:
            lines = filehandle.readlines()
            lines = [ line.replace("\n", "") for line in lines]
            return Ok(lines)
    except BaseException as error:
        return Err(f"error when reading .txt file: {error}")
        

