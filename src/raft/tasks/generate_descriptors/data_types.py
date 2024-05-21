"""TODO"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DeploymentIndex:
    """Class representing search results for a deployment."""

    name: str
    messages: list[Path]
    cameras: list[Path]


@dataclass
class DeploymentIndexGroup:
    """Class representing a group of deployment files."""

    name: str
    directory: Path
    deployments: list[DeploymentIndex]
