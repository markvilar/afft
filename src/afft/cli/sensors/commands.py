"""CLI commands for sensor-specific processing."""

import click

from .actions import dispatch_process_tracklink_usbl


@click.group()
@click.pass_context
def sensors_group(context: click.Context) -> None:
    """CLI group for sensor-specific processing commands."""
    context.ensure_object(dict)


@sensors_group.command()
@click.argument("usbl_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("pressure_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
@click.option(
    "--ship-sensor-configs",
    "ship_sensor_configs",
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
    ship_sensor_configs: str,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL data.

    USBL_FILE: CSV file with TrackLink USBL observations (bearing, range, ship
    position).

    PRESSURE_FILE: CSV file with pressure sensor depth readings.

    OUTPUT_FILE: destination CSV path for the processed output.
    """
    dispatch_process_tracklink_usbl(
        usbl_file,
        pressure_file,
        output_file,
        ship_sensor_configs,
        deployment_label,
    )
