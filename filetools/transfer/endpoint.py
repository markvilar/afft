from dataclasses import dataclass
from pathlib import Path

@dataclass
class Endpoint():
    host: str
    path: Path

    def as_string(self) -> str:
        """ Return the string representation of the endpoint. """
        return self.host + ":" + str(self.path)
