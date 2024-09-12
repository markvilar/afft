"""Entrypoint for command-line interface services."""

import click

from ..utils.log import init_logger

from .message_cli import message_services


# Create the main CLI as a collection of task specific CLIs
cli_services = click.CommandCollection(sources=[message_services])


def main():
    """Main entrypoint for the command-line interface."""

    init_logger()
    cli_services()


if __name__ == "__main__":
    main()
