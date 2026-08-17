"""Entrypoint for command-line interface services."""

import click

from afft.utils.log import init_logger

from .benthloc.commands import benthloc_group as benthloc_commands
from .bundle.commands import bundle_group as bundle_commands
from .database.commands import database_group as database_commands
from .deployment.commands import deployment_group as deployment_commands
from .sensors.commands import sensors_group as sensor_commands
from .squidle.commands import squidle_group as squidle_commands
from .tasks.commands import task_group as task_commands


@click.group()
def cli() -> None:
    """Main CLI command group."""
    pass


cli.add_command(benthloc_commands, name="benthloc")
cli.add_command(bundle_commands, name="bundle")
cli.add_command(database_commands, name="database")
cli.add_command(deployment_commands, name="deployment")
cli.add_command(sensor_commands, name="sensors")
cli.add_command(squidle_commands, name="squidle")
cli.add_command(task_commands, name="tasks")


def main() -> None:
    """Main entrypoint for the command-line interface."""
    init_logger()
    cli()


if __name__ == "__main__":
    main()
