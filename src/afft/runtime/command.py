"""Module for commands."""

from dataclasses import dataclass


@dataclass
class Command:
    """Class that represents a command."""

    command: str
    arguments: list[str]
