"""Module for formatting AUV messages including reading, preprocessing,
parsing, and exporting."""

import argparse

from pathlib import Path
from typing import List

from loguru import logger

from .config import (
    MessagePaths,
    MessageProtocol,
    configure_message_paths,
    configure_message_protocol,
    validate_message_paths,
    validate_message_protocol,
)

from .line_processors import Line, LineProcessor, process_message_lines
from .message_readers import read_message_lines


def read_and_accumulate_lines(paths: MessagePaths) -> List[Line]:
    """Executes message processing."""

    # Get absolute file paths
    message_files: List[Path] = [paths.directories.data / file for file in paths.files.messages]

    lines: List[Line] = list()
    for file in message_files:
        new_lines: List[Line] = read_message_lines(file).unwrap()
        logger.info(f"Read lines: {len(new_lines)}")
        lines.extend(new_lines)

    logger.info(f"Total amount of lines read: {len(lines)}")

    return lines


def process_messages(arguments: List[str]) -> None:
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
    processed_lines: List[Line] = process_message_lines(lines)

    logger.info(f"Count, lines:           {len(lines)}")
    logger.info(f"Count, processed lines: {len(processed_lines)}")

    # TODO: Process messages

    raise NotImplementedError
