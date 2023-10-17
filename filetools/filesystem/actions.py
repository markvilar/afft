import os
import shutil

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)
Result = Tuple[T, Optional[E]]

@dataclass
class MoveEntry():
    """ Entry for the filesystem move action. """
    source: Path
    destination: Path

def copy(source: Path, destination: Path) -> Result[bool, Exception]:
    """ Copy a source to a destination. """
    try:
        shutil.copy(source, destination)
    except Exception as exception:
        return False, exception
    return True, None

def move(source: Path, destination: Path) -> Result[bool, Exception]:
    """ Move a source to a destination. """
    try:
        shutil.move(source, destination)
    except Exception as exception:
        return False, exception
    return True, None


