"""Main script - Entry point for executing tasks."""

import sys

from raft.runtime import Command
from raft.utils.log import init_logger, logger

from raft.tasks.camera_processing import invoke_camera_formatting
from raft.tasks.generate_descriptors import invoke_group_descriptor_generation
from raft.tasks.message_processing import invoke_message_processing


def main():
    """Entry point for the command-line interface."""

    # Initialize logger with level, format, and sinks
    init_logger()

    command, *arguments = sys.argv[1:]
    command = Command(command, arguments)

    match command:
        case Command(command="process_messages"):
            invoke_message_processing(command.arguments)
        case Command(command="process_cameras"):
            invoke_camera_formatting(command.arguments)
        case Command(command="describe"):
            invoke_group_descriptor_generation(command.arguments)

        case _:
            logger.error(f"invalid command: {command.command}")


if __name__ == "__main__":
    main()
