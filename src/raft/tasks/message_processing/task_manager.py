"""Module for formatting AUV messages including reading, preprocessing,
parsing, and exporting."""

import argparse
import re

from pathlib import Path
from typing import Dict, List

from loguru import logger

from .config import (
    MessagePaths,
    MessageProtocol,
    configure_message_paths,
    configure_message_protocol,
    validate_message_paths,
    validate_message_protocol,
)

from .line_processors import LineProcessor, process_message_lines
from .line_readers import read_message_lines
from .interfaces import Line

# TEMPORARY: Import protocol
from raft.services.sirius_messages.data_parsers import (
    PROTOCOL_DEV,
    PROTOCOL_V1,
    PROTOCOL_V2,
)
from raft.services.sirius_messages.parsers import parse_message


def read_and_accumulate_lines(paths: MessagePaths) -> List[Line]:
    """Executes message processing."""

    # Get absolute file paths
    message_files: List[Path] = [
        paths.directories.data / file for file in paths.files.messages
    ]

    lines: List[Line] = list()
    for file in message_files:
        new_lines: List[Line] = read_message_lines(file).unwrap()
        logger.info(f"Read lines: {len(new_lines)}")
        lines.extend(new_lines)

    logger.info(f"Total amount of lines read: {len(lines)}")

    return lines


def handle_messages(lines: List[Line], protocol: Dict) -> Dict[str, object]:
    """Temporary."""

    for line in lines:
        message = parse_message(line, PROTOCOL_DEV)

        # for identifier, parser in protocol_v1.items():
        # parser(line)

    raise NotImplementedError


def invoke_message_formatting(arguments: List[str]) -> None:
    """Executor for processing messages."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        type=Path,
        help="configuration file for paths, i.e. directories and files",
    )
    parser.add_argument(
        "protocol",
        type=Path,
        help="configuration file for protocol",
    )

    arguments = parser.parse_args(arguments)

    # Set up configuration - directories, files, andand  parameters
    message_paths: MessagePaths = configure_message_paths(arguments.paths)
    message_protocol: MessageProtocol = configure_message_protocol(arguments.protocol)

    # Validate configuration
    message_paths: MessagePaths = validate_message_paths(message_paths).unwrap()

    # TODO: Implement
    # message_protocol: MessageProtocol = validate_message_protocol(message_protocol).unwrap()

    # Read message lines from files
    lines: List[Line] = read_and_accumulate_lines(message_paths)
    cleaned_lines: List[Line] = process_message_lines(lines)

    # Parse messages
    handle_messages(cleaned_lines, PROTOCOL_DEV)
