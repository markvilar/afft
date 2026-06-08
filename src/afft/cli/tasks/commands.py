"""
CLI commands for invoking data processing tasks.
"""

from datetime import datetime

import click

from .actions import (
    dispatch_batch_process_renav,
    dispatch_clip_tables,
    dispatch_collect_renav_stereo_poses,
    dispatch_correct_pressure_tide,
    dispatch_process_renav,
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
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Renav stereo pose estimate file to process",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the processed output as CSV",
)
def process_renav_poses(input_file: str, output_file: str) -> None:
    """Process a Renav stereo pose estimate file and write to CSV."""
    dispatch_process_renav(input_file, output_file)


@task_group.command()
@click.option(
    "--input",
    "input_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory containing Renav stereo pose estimate files",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write the processed CSV files into",
)
@click.option(
    "--pattern",
    type=str,
    default="*.txt",
    show_default=True,
    help="glob pattern to select input files",
)
def batch_process_renav_poses(input_dir: str, output_dir: str, pattern: str) -> None:
    """Batch process Renav stereo pose estimate files in a directory."""
    dispatch_batch_process_renav(input_dir, output_dir, pattern)


@task_group.command()
@click.option(
    "--input",
    "root_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="root directory containing deployment subdirectories",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write the relabelled files into",
)
@click.option(
    "--deployment-suffix",
    "deployment_suffix",
    type=str,
    default="_deployment_data",
    show_default=True,
    help="suffix stripped from deployment directory names to form the label",
)
@click.option(
    "--appendix",
    type=str,
    default="_renav_stereo_poses.txt",
    show_default=True,
    help="suffix appended to the deployment label to form the output filename",
)
@click.option(
    "--tiebreak-margin",
    "tiebreak_margin",
    type=float,
    default=0.03,
    show_default=True,
    help="fractional row-count margin within which the most recent file wins",
)
def collect_renav_stereo_poses(
    root_dir: str,
    output_dir: str,
    deployment_suffix: str,
    appendix: str,
    tiebreak_margin: float,
) -> None:
    """Collect and relabel Renav stereo pose estimate files by deployment."""
    dispatch_collect_renav_stereo_poses(
        root_dir,
        output_dir,
        deployment_suffix,
        appendix,
        tiebreak_margin,
    )


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
    "--group-by",
    "grouping_strategy",
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
    grouping_strategy: str,
) -> None:
    """Run the telemetry processing pipeline on CSV tables in SOURCE_DIR."""
    dispatch_process_telemetry(
        source_dir, output_dir, config_file, pattern, grouping_strategy
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
