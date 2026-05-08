"""Module for file transfer dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Endpoint:
    """Class representing an endpoint."""

    host: str
    path: Path

    def as_string(self) -> str:
        """Return the string representation of the endpoint."""
        return self.host + ":" + str(self.path)


def create_endpoint_from_string(string: str) -> Endpoint:
    """
    Create an endpoint from a string consisting of hostname and path on the
    format <hostname>:<path>.
    """
    splits = string.split(":")
    if not len(splits) == 2:
        raise ValueError(f"invalid endpoint string: {string}")

    return Endpoint(host=splits[0], path=splits[1])


@dataclass(unsafe_hash=True)
class FileSearch:
    """Data class to represent a file search."""

    source: Path
    destination: Path
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
