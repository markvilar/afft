"""
CLI commands for invoking data processing tasks.
"""

import click

from .actions import dispatch_correct_pressure_tide


@click.group()
@click.pass_context
def task_group(context: click.Context) -> None:
    """CLI group for invoking data processing tasks."""
    context.ensure_object(dict)


@task_group.command()
@click.argument("reading_file", type=click.Path(exists=True))
@click.argument("sealevel_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option(
    "--verbose", is_flag=True, default=False, help="enable debug logging"
)
def correct_pressure_tide(
    reading_file: str,
    sealevel_file: str,
    output_file: str,
    verbose: bool,
) -> None:
    """Tide-correct pressure sensor depth readings."""
    dispatch_correct_pressure_tide(
        reading_file,
        sealevel_file,
        output_file,
        verbose,
    )
