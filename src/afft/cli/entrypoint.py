"""Entrypoint for command-line interface services."""

import click

from afft.utils.log import init_logger

from .database.commands import database_group as database_commands
from .messages.commands import message_group as message_commands
from .renav.commands import renav_group as renav_commands
from .sensors.commands import sensors_group as sensor_commands
from .squidle.commands import squidle_group as squidle_commands
from .tasks.commands import task_group as task_commands


@click.group()
def cli() -> None:
    """Main CLI command group."""
    pass


cli.add_command(database_commands, name="database")
cli.add_command(message_commands, name="messages")
cli.add_command(renav_commands, name="renav")
cli.add_command(sensor_commands, name="sensors")
cli.add_command(squidle_commands, name="squidle")
cli.add_command(task_commands, name="tasks")


def main() -> None:
    """Main entrypoint for the command-line interface."""
    init_logger()
    cli()


if __name__ == "__main__":
    main()
