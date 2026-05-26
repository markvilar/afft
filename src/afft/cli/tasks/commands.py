"""
CLI commands for invoking data processing tasks.
"""

from datetime import datetime

import click

from .actions import (
    dispatch_clip_tables,
    dispatch_correct_pressure_tide,
    dispatch_process_telemetry,
)

_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def _parse_timestamp(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> datetime:
    try:
        return datetime.strptime(value, _TIMESTAMP_FORMAT)
    except ValueError:
        raise click.BadParameter(
            f"expected format YYYYMMDD_HHmmSS, got {value!r}"
        )


@click.group()
@click.pass_context
def task_group(context: click.Context) -> None:
    """CLI group for invoking data processing tasks."""
    context.ensure_object(dict)


@task_group.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_dir", type=click.Path(file_okay=False))
@click.option(
    "--start",
    type=str,
    required=True,
    callback=_parse_timestamp,
    is_eager=True,
    help="start of time interval (YYYYMMDD_HHmmSS, inclusive)",
)
@click.option(
    "--end",
    type=str,
    required=True,
    callback=_parse_timestamp,
    is_eager=True,
    help="end of time interval (YYYYMMDD_HHmmSS, inclusive)",
)
@click.option(
    "--pattern",
    type=str,
    default="*.csv",
    show_default=True,
    help="glob pattern to select files in source_dir",
)
@click.option(
    "--timestamp-column",
    "timestamp_column",
    type=str,
    default="timestamp",
    show_default=True,
    help="column to filter on",
)
def clip_tables(
    source_dir: str,
    output_dir: str,
    start: datetime,
    end: datetime,
    pattern: str,
    timestamp_column: str,
) -> None:
    """Clip CSV files in SOURCE_DIR to [START, END] and write to OUTPUT_DIR."""
    dispatch_clip_tables(
        source_dir,
        output_dir,
        start,
        end,
        pattern,
        timestamp_column,
    )


@task_group.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_dir", type=click.Path(file_okay=False))
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="TOML pipeline config file",
)
@click.option(
    "--pattern",
    type=str,
    default="*.csv",
    show_default=True,
    help="glob pattern to select input files in source_dir",
)
@click.option(
    "--strategy",
    type=click.Choice(["prefix", "suffix"], case_sensitive=False),
    default="prefix",
    show_default=True,
    help="how to derive context keys from filenames",
)
def process_telemetry(
    source_dir: str,
    output_dir: str,
    config_file: str,
    pattern: str,
    strategy: str,
) -> None:
    """Run the telemetry processing pipeline on CSV tables in SOURCE_DIR."""
    dispatch_process_telemetry(
        source_dir, output_dir, config_file, pattern, strategy
    )


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
