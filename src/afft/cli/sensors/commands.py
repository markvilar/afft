"""CLI commands for sensor-specific processing."""

import click

from .actions import invoke_parse_tracklink_log
from .actions import invoke_process_evologics_usbl
from .actions import invoke_process_tracklink_usbl_from_logs
from .actions import invoke_process_tracklink_usbl_from_messages


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
    invoke_parse_tracklink_log(source_file, output_file)


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
    "--descriptor-file",
    "descriptor_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the deployment descriptors TOML file.",
)
@click.option(
    "--deployment-label",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to select from --descriptor-file.",
)
@click.option(
    "--ignore-extrinsics",
    "ignore_extrinsics",
    is_flag=True,
    default=False,
    help="Use zero extrinsics instead of the calibrated values from the descriptor.",
)
@click.option(
    "--horizontal-position-std",
    "horizontal_position_std",
    type=float,
    default=None,
    help="Override the 1σ horizontal position uncertainty in metres.",
)
@click.option(
    "--depth-position-std",
    "depth_position_std",
    type=float,
    default=None,
    help="Override the 1σ depth position uncertainty in metres.",
)
def process_tracklink_usbl_from_messages(
    usbl_file: str,
    pressure_file: str,
    output_file: str,
    descriptor_file: str,
    deployment_label: str,
    ignore_extrinsics: bool,
    horizontal_position_std: float | None,
    depth_position_std: float | None,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink AUV messages."""
    invoke_process_tracklink_usbl_from_messages(
        usbl_file,
        pressure_file,
        output_file,
        descriptor_file,
        deployment_label,
        ignore_extrinsics=ignore_extrinsics,
        horizontal_position_std=horizontal_position_std,
        depth_position_std=depth_position_std,
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
    "--descriptor-file",
    "descriptor_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the deployment descriptors TOML file.",
)
@click.option(
    "--deployment-label",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to select from --descriptor-file.",
)
@click.option(
    "--ignore-extrinsics",
    "ignore_extrinsics",
    is_flag=True,
    default=False,
    help="Use zero extrinsics instead of the calibrated values from the descriptor.",
)
@click.option(
    "--horizontal-position-std",
    "horizontal_position_std",
    type=float,
    default=None,
    help="Override the 1σ horizontal position uncertainty in metres.",
)
@click.option(
    "--depth-position-std",
    "depth_position_std",
    type=float,
    default=None,
    help="Override the 1σ depth position uncertainty in metres.",
)
def process_tracklink_usbl_from_logs(
    usbl_file: str,
    output_file: str,
    descriptor_file: str,
    deployment_label: str,
    ignore_extrinsics: bool,
    horizontal_position_std: float | None,
    depth_position_std: float | None,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL log entries."""
    invoke_process_tracklink_usbl_from_logs(
        usbl_file,
        output_file,
        descriptor_file,
        deployment_label,
        ignore_extrinsics=ignore_extrinsics,
        horizontal_position_std=horizontal_position_std,
        depth_position_std=depth_position_std,
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
    "--descriptor-file",
    "descriptor_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the deployment descriptors TOML file.",
)
@click.option(
    "--deployment-label",
    "deployment_label",
    type=str,
    required=True,
    help="Deployment label to select from --descriptor-file.",
)
@click.option(
    "--ignore-extrinsics",
    "ignore_extrinsics",
    is_flag=True,
    default=False,
    help="Use zero extrinsics instead of the calibrated values from the descriptor.",
)
@click.option(
    "--horizontal-position-std",
    "horizontal_position_std",
    type=float,
    default=None,
    help="Override the 1σ horizontal position uncertainty in metres.",
)
@click.option(
    "--depth-position-std",
    "depth_position_std",
    type=float,
    default=None,
    help="Override the 1σ depth position uncertainty in metres.",
)
def process_evologics_usbl(
    usbl_file: str,
    output_file: str,
    descriptor_file: str,
    deployment_label: str,
    ignore_extrinsics: bool,
    horizontal_position_std: float | None,
    depth_position_std: float | None,
) -> None:
    """Convert Evologics USBL data to the USBL output schema."""
    invoke_process_evologics_usbl(
        usbl_file,
        output_file,
        descriptor_file,
        deployment_label,
        ignore_extrinsics=ignore_extrinsics,
        horizontal_position_std=horizontal_position_std,
        depth_position_std=depth_position_std,
    )
