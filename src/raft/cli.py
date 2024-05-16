"""Main script - Entry point for executing tasks."""

import sys

from raft.runtime import Command
from raft.utils.log import init_logger

from raft.tasks.camera_processing import process_cameras
from raft.tasks.message_processing import process_messages


def main():
    """Entry point for the command-line interface."""

    # Initialize logger with level, format, and sinks
    init_logger()

    command, *arguments = sys.argv[1:]
    command = Command(command, arguments)

    match command:
        case Command(command="process_messages"):
            process_messages(command.arguments)
        case Command(command="process_cameras"):
            process_cameras(command.arguments)


if __name__ == "__main__":
    main()
