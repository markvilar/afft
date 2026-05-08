"""Entrypoint for command-line interface services."""

import click

from afft.utils.log import init_logger

from .database.commands import database_group as database_commands 
from .messages.commands import message_group as message_commands


@click.group()
def cli() -> None:
    """Main CLI command group."""
    pass


cli.add_command(database_commands, name="database")
cli.add_command(message_commands, name="messages")


def main():
    """Main entrypoint for the command-line interface."""
    init_logger()
    cli()


if __name__ == "__main__":
    main()
