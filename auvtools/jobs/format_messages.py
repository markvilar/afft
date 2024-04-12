"""Module for formatting AUV messages including reading, preprocessing,
parsing, and exporting."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List


@dataclass
class MessageFormattingData:
    """Data class for message formatting data."""

    name: str
    message_files: List[Path]
    output_file: Path


# NOTE: Temporary
Message = object
Messages = List[Message]

Identifier = str

# Reader types
MessageLine = str
MessageLines = List[MessageLine]

# Parser types
MessageGroups = Dict[Identifier, Messages]

# Formatting job interfaces
MessageReader = Callable[[None], MessageLines]
MessageParser = (Callable[[MessageLines], MessageGroups],)
MessageExporter = Callable[[MessageGroups], bool]


def format_and_export_messages(
    reader: MessageReader,
    parser: MessageParser,
    exporter: MessageExporter,
) -> None:
    """Job handler for formatting messages."""

    lines: MessageLines = reader()
    message_groups: MessageGroups = parser(lines)
    export_status: bool = export(message_groups)
