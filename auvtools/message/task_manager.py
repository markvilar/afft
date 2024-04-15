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
from .message_readers import read_message_lines


def execute_message_processing_task(paths: MessagePaths) -> None:
    """Executes message processing."""

    # Get absolute file paths
    message_files: List[Path] = [paths.directories.data / file for file in paths.files.messages]

    lines: List[str] = list()
    for file in message_files:
        new_lines: List[str] = read_message_lines(file).unwrap()
        logger.info(f"Read lines: {len(new_lines)}")
        lines.extend(new_lines)

    logger.info(f"Total amount of lines read: {len(lines)}")

    # TODO: Invoke message formatting job

    raise NotImplementedError


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

    logger.info(message_paths)
    logger.info(message_protocol)

    # Execute processing
    execute_message_processing_task(message_paths)
