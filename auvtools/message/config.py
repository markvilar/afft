"""Module for configuration of """

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from dotenv import dotenv_values
from result import Ok, Err, Result

from auvtools.io import read_toml


DATA_PATH_KEY = "MESSAGE_INPUT_ROOT"
OUTPUT_PATH_KEY = "MESSAGE_OUTPUT_ROOT"

INPUT_FILE_KEY = "messages"
OUTPUT_FILE_KEY = "output"

@dataclass
class Directories:
    """Class representing directory paths."""

    data: Path
    output: Path


@dataclass
class Files:
    """Class representing file paths."""

    messages: List[Path]
    output: Path


@dataclass
class MessagePaths:
    """Class representing a message paths."""

    directories: Directories
    files: Files


def configure_directories(config: Dict) -> Directories:
    """Prepares the path configuration for the task."""

    variables = dotenv_values(".env")
    input_root: str = variables[DATA_PATH_KEY]
    output_root: str = variables[OUTPUT_PATH_KEY]

    message_path = Path(f"{input_root}/{config['data']}")
    output_path = Path(f"{output_root}/{config['output']}")

    return Directories(data=message_path, output=output_path)


def configure_files(config: Dict) -> Files:
    """Prepares the file configuration for the task."""

    message_files = [Path(file) for file in config[INPUT_FILE_KEY]]
    output_file = Path(config[OUTPUT_FILE_KEY])

    return Files(messages=message_files, output=output_file)


def configure_message_paths(path: Path) -> MessagePaths:
    """Configures message paths from the given configuration file."""

    config: Dict = read_toml(path).unwrap()

    directories: Files = configure_directories(config["directories"])
    files: Files = configure_files(config["files"])

    return MessagePaths(directories=directories, files=files)


def validate_message_paths(paths: MessagePaths) -> Result[MessagePaths, str]:
    """Validates the message paths by checking the existance of directories and files. """

    if not paths.directories.data.exists():
        return Err("data directory does not exist")

    message_files = [paths.directories.data / file for file in paths.files.messages]
    for message_file in message_files:
        if not message_file.exists():
            return Err(f"message file does not exist: {message_file}")

    return Ok(paths)


@dataclass
class MessageProtocol:
    """Class representing a message processor."""

    identifiers: List[str]


def configure_message_protocol(path: Path) -> MessageProtocol:
    """Configures a message protocol from the given configuration file."""

    config: Dict = read_toml(path).unwrap()

    identifiers = config["messages"]["identifiers"]

    return MessageProtocol(identifiers)

def validate_message_protocol(protocol: MessageProtocol) -> Result[MessageProtocol, str]:
    """Validates the message protocol. """

    return Err("not implemented")

