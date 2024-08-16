"""Module with data types for message parsing tasks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class MessageParseContext:
    """TODO"""

    input_file: Path
    output_file: Path
    protocol_file: Path


type MessageLoader = Callable[[None], list[str]]


class MessageParseData:
    """TODO"""

    message_loader: Callable
    protocol_builder: Callable
    message_saver: Callable
