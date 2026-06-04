"""CLI commands for sensor-specific processing."""

import click

from .actions import dispatch_parse_tracklink_log
from .actions import dispatch_process_evologics_usbl
from .actions import dispatch_process_tracklink_usbl_from_logs
from .actions import dispatch_process_tracklink_usbl_from_messages


@click.group()
@click.pass_context
def sensors_group(context: click.Context) -> None:
    """CLI group for sensor-specific processing commands."""
    context.ensure_object(dict)


@sensors_group.command()
@click.option(
    "--source-file",
    "source_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Merged TrackLink USBL log file (.txt).",
)
@click.option(
    "--output-file",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="Destination CSV path for the parsed fixes.",
)
def parse_tracklink_log(
    source_file: str,
    output_file: str,
) -> None:
    """Parse a merged TrackLink USBL log file into a CSV of fixes."""
    dispatch_parse_tracklink_log(source_file, output_file)


@sensors_group.command()
@click.option(
    "--usbl-file",
    "usbl_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="CSV file with TrackLink USBL observations (bearing, range, ship position).",
)
@click.option(
    "--pressure-file",
    "pressure_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="CSV file with pressure sensor depth readings.",
)
@click.option(
    "--output-file",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="Destination CSV path for the processed output.",
)
@click.option(
    "--deployment-configs",
    "deployment_configs",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="TOML file containing ship sensor configurations and deployment mappings.",
)
@click.option(
    "--deployment",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to look up in the ship sensor configurations file.",
)
def process_tracklink_usbl_from_messages(
    usbl_file: str,
    pressure_file: str,
    output_file: str,
    deployment_configs: str,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink AUV messages."""
    dispatch_process_tracklink_usbl_from_messages(
        usbl_file,
        pressure_file,
        output_file,
        deployment_configs,
        deployment_label,
    )


@sensors_group.command()
@click.option(
    "--usbl-file",
    "usbl_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="CSV file with merged TrackLink USBL log entries (ship position, ship attitude, target XYZ).",
)
@click.option(
    "--output-file",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="Destination CSV path for the processed output.",
)
@click.option(
    "--deployment-configs",
    "deployment_configs",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="TOML file containing ship sensor configurations and deployment mappings.",
)
@click.option(
    "--deployment",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to look up in the ship sensor configurations file.",
)
@click.option(
    "--ignore-extrinsics",
    "ignore_extrinsics",
    is_flag=True,
    default=False,
    help="Use zero extrinsics instead of the calibrated values from the deployment config.",
)
def process_tracklink_usbl_from_logs(
    usbl_file: str,
    output_file: str,
    deployment_configs: str,
    deployment_label: str,
    ignore_extrinsics: bool,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL log entries."""
    dispatch_process_tracklink_usbl_from_logs(
        usbl_file,
        output_file,
        deployment_configs,
        deployment_label,
        ignore_extrinsics=ignore_extrinsics,
    )


@sensors_group.command()
@click.option(
    "--usbl-file",
    "usbl_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="CSV file with parsed Evologics USBL observations.",
)
@click.option(
    "--output-file",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="Destination CSV path for the processed output.",
)
@click.option(
    "--deployment-configs",
    "deployment_configs",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="TOML file containing ship sensor configurations and deployment mappings.",
)
@click.option(
    "--deployment",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to look up in the ship sensor configurations file.",
)
def process_evologics_usbl(
    usbl_file: str,
    output_file: str,
    deployment_configs: str,
    deployment_label: str,
) -> None:
    """Convert Evologics USBL data to the unified USBL output schema."""
    dispatch_process_evologics_usbl(
        usbl_file,
        output_file,
        deployment_configs,
        deployment_label,
    )
