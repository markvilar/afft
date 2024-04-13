"""Module for formatting AUV messages including reading, preprocessing,
parsing, and exporting."""

import argparse

from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import dotenv_values
from loguru import logger

from auvtools.io import read_toml
from auvtools.messages.message_readers import read_message_lines_and_concatenate


@dataclass
class FileConfig:
    """Class representing message files."""
    messages: List[Path]
    output: Path

@dataclass
class ProcessorConfig:
    """Class representing message processor."""
    messages: List[str]

@dataclass
class MessageFormattingData:
    """Data class for message formatting data."""

    name: str
    message_files: List[Path]
    output_file: Path


def configure_paths(config: Path) -> FileConfig:
    """Prepares the path configuration for the task."""

    variables = dotenv_values(".env")

    input_root = Path(variables["MESSAGE_INPUT_DIRECTORY"])
    output_root = Path(variables["MESSAGE_OUTPUT_DIRECTORY"])

    paths = read_toml(config).unwrap()

    directories = paths["directories"]
    files = paths["files"]
   
    # Create absolute directory paths
    message_directory = input_root / directories["messages"]
    output_directory = output_root / directories["output"]

    # Create absolute file paths
    message_files = [message_directory / file for file in files["messages"]]
    output_file = output_directory / files["output"]

    return FileConfig(messages=message_files, output=output_file)


def configure_processor(processor_config: Path) -> ProcessorConfig:
    """Prepares the processor configuration for the task."""
    read_toml(processor_config).unwrap()
    raise NotImplementedError


def configure_message_processing(path_config: Path, processor_config: Path) -> None:
    """Prepares config by loading environment variables and configuration files."""

    # Read configuration files
    paths = configure_paths(path_config)
    protocol = configure_processor(processor_config)

    raise NotImplementedError


def execute_message_processing_task() -> None:
    """Executes message processing."""
    # Read message files
    lines: List[str] = read_message_lines_and_concatenate(
        formatting_data.message_files
    ).unwrap()

    logger.info(f"Read and concatenated: {len(lines)} message lines")

    # TODO: Invoke message formatting job

    raise NotImplementedError


def process_messages(arguments: List[str]) -> None:
    """Executor for processing messages."""
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data", 
        type=Path, 
        help="data configuration file, i.e. files and paths"
    )
    parser.add_argument(
        "processor", 
        type=Path, 
        help="processor configuration file, i.e. message set and descriptors"
    )

    namespace = parser.parse_args(arguments)

    logger.info(namespace)

    # TODO: Set up configuration
    config = configure_message_processing(namespace.data, namespace.processor)

    # TODO: Execute processing
    execute_message_processing_task()

    raise NotImplementedError
