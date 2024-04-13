"""Main script - Entry point for executing tasks."""

import sys

from auvtools.session import Command

# Tasks
from auvtools.tasks.process_cameras import process_cameras
from auvtools.tasks.process_messages import process_messages


def main():
    """Entry point for invoking tasks."""

    command, *arguments = sys.argv[1:]
    command = Command(command, arguments)

    match command:
        case Command(command="process_messages", arguments=any):
            process_messages(command.arguments)
        case Command(command="process_cameras", arguments=[config]):
            process_cameras(command.arguments)


if __name__ == "__main__":
    main()
