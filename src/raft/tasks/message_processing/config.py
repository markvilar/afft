"""Module for configuration of message merge tasks."""

from dataclasses import dataclass
from pathlib import Path

from result import Ok, Err, Result

from raft.io import read_toml
from raft.utils.log import logger


@dataclass
class Directories:
    """Class representing"""

    input: Path
    output: Path


@dataclass
class MessageMergeConfig:
    """Class representing a message merge task."""

    name: str
    message_files: list[Path]
    directories: Directories


@dataclass
class MessageMergeBatch:
    """Class representing a batch of message merge configs."""

    subtasks: list[MessageMergeConfig]


def configure_task(
    input_directory: Path, output_directory: Path, config: Path
) -> MessageMergeBatch:
    """Create a task configuration."""

    data: dict = read_toml(config).unwrap()

    subtasks: list[MessageMergeConfig] = list()
    for subtask in data["deployment"]:
        logger.info(subtask)

        subtasks.append(
            MessageMergeConfig(
                name=subtask["name"],
                message_files=[Path(file) for file in subtask["message_files"]],
                directories=Directories(input_directory, output_directory),
            )
        )

    return MessageMergeBatch(subtasks)
