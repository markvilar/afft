"""Functionality for commands."""

from dataclasses import dataclass
from typing import List, Callable

type Command = str
type Action = Callable[[], None]


@dataclass
class Command:
    """Class that represents a command."""

    command: str
    arguments: List[str]
