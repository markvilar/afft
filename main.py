"""Main script - Entry point for executing tasks."""

import sys

from raft.session import Command

from raft.camera import process_cameras
from raft.message import process_messages

from raft.utils.log import init_logger


def main():
    """Entry point for invoking tasks."""

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
