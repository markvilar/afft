"""Entrypoint for invoking tasks through the command-line interface."""

import sys

from raft.runtime import Command
from raft.utils.log import init_logger, logger

from raft.tasks.camera_filtering import invoke_camera_filtering
from raft.tasks.export_metafile import invoke_metafile_export
from raft.tasks.generate_metafile import invoke_metafile_generation
from raft.tasks.message_parsing import invoke_message_parsing


def main():
    """Entry point for the command-line interface."""

    # Initialize logger with level, format, and sinks
    init_logger()

    command, *arguments = sys.argv[1:]
    command = Command(command, arguments)

    match command:
        case Command(command="generate"):
            invoke_metafile_generation(command.arguments)
        case Command(command="metafile-export"):
            invoke_metafile_export(command.arguments)
        case Command(command="filter-cameras"):
            invoke_camera_filtering(command.arguments)
        case Command(command="parse-messages"):
            invoke_message_parsing(command)
        case _:
            logger.error(f"invalid command: {command.command}")


if __name__ == "__main__":
    main()
