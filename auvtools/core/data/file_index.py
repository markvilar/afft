from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass
class FileIndex():
    """ """
    root: Path
    children: Dict[str, Path]
