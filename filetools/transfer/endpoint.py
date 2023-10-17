from dataclasses import dataclass
from pathlib import Path

@dataclass
class Endpoint():
    host: str
    path: Path
