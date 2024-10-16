"""Entrypoint for command-line interface services."""

import click

from afft.utils.log import init_logger

from .database_cli import database_cli
from .message_cli import message_cli


# Create the main CLI as a collection of task specific CLIs
cli_services = click.CommandCollection(
    sources=[
        database_cli,
        message_cli,
    ]
)


def main():
    """Main entrypoint for the command-line interface."""

    init_logger()
    cli_services()


if __name__ == "__main__":
    main()
