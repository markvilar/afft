"""Main script - Entry point for executing tasks."""

import sys

from raft.runtime import Command
from raft.utils.log import init_logger, logger

from raft.tasks.camera_processing import invoke_camera_formatting
from raft.tasks.message_merge import invoke_message_merging


def main():
    """Entry point for the command-line interface."""

    # Initialize logger with level, format, and sinks
    init_logger()

    command, *arguments = sys.argv[1:]
    command = Command(command, arguments)

    match command:
        case Command(command="merge_messages"):
            invoke_message_merging(command.arguments)
        case Command(command="format_cameras"):
            invoke_camera_formatting(command.arguments)
        case _:
            logger.error(f"invalid command: {command.command}")


if __name__ == "__main__":
    main()
