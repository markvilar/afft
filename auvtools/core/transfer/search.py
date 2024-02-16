from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass(unsafe_hash=True)
class FileSearch():
    """ Data class to represent a file search. """
    source: Path
    destination: Path
    includes : List[str] = field(default_factory=list)
    excludes : List[str] = field(default_factory=list)
