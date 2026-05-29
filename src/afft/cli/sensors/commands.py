"""CLI commands for sensor-specific processing."""

import click

from .actions import dispatch_process_tracklink_usbl


@click.group()
@click.pass_context
def sensors_group(context: click.Context) -> None:
    """CLI group for sensor-specific processing commands."""
    context.ensure_object(dict)


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
def process_tracklink_usbl(
    usbl_file: str,
    pressure_file: str,
    output_file: str,
    deployment_configs: str,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL data."""
    dispatch_process_tracklink_usbl(
        usbl_file,
        pressure_file,
        output_file,
        deployment_configs,
        deployment_label,
    )
