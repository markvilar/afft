"""CLI commands for Renav processing tasks."""

import click

from .actions import (
    dispatch_batch_correct_renav_poses,
    dispatch_batch_process_renav,
    dispatch_collect_renav_stereo_poses,
    dispatch_correct_renav_poses,
    dispatch_process_renav,
    dispatch_transform_camera_poses,
    dispatch_transform_camera_poses_batch,
)


@click.group()
@click.pass_context
def renav_group(context: click.Context) -> None:
    """CLI group for Renav processing commands."""
    context.ensure_object(dict)


@renav_group.command()
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
def process_poses(input_file: str, output_file: str) -> None:
    """Process a Renav stereo pose estimate file and write to CSV."""
    dispatch_process_renav(input_file, output_file)


@renav_group.command()
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
def batch_process_poses(input_dir: str, output_dir: str, pattern: str) -> None:
    """Batch process Renav stereo pose estimate files in a directory."""
    dispatch_batch_process_renav(input_dir, output_dir, pattern)


@renav_group.command()
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
def collect_stereo_poses(
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


@renav_group.command()
@click.option(
    "--target",
    "target_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="target camera pose CSV whose latitude/longitude will be replaced",
)
@click.option(
    "--source",
    "source_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="source camera pose CSV to take latitude and longitude from",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the corrected output as CSV",
)
def correct_poses(
    target_file: str,
    source_file: str,
    output_file: str,
) -> None:
    """Correct Renav camera poses with source camera pose latitude/longitude."""
    dispatch_correct_renav_poses(target_file, source_file, output_file)


@renav_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="camera pose CSV to transform to vehicle reference-point poses",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the vehicle poses as CSV",
)
@click.option(
    "--vehicle-config",
    "vehicle_config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="vehicle TOML config containing stereo camera extrinsics",
)
def transform_poses(
    input_file: str,
    output_file: str,
    vehicle_config_file: str,
) -> None:
    """Transform camera poses to vehicle reference-point poses using stereo extrinsics."""
    dispatch_transform_camera_poses(
        input_file, output_file, vehicle_config_file
    )


@renav_group.command()
@click.option(
    "--input-dir",
    "input_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory containing camera pose CSV files",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write vehicle pose CSV files into",
)
@click.option(
    "--vehicle-config",
    "vehicle_config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="vehicle TOML config containing stereo camera extrinsics",
)
@click.option(
    "--input-suffix",
    "input_suffix",
    type=str,
    default="_renav_stereo_poses.csv",
    show_default=True,
    help="suffix stripped from input filenames to derive the deployment label",
)
@click.option(
    "--output-suffix",
    "output_suffix",
    type=str,
    default="_vehicle_poses.csv",
    show_default=True,
    help="suffix appended to the deployment label to form the output filename",
)
def batch_transform_poses(
    input_dir: str,
    output_dir: str,
    vehicle_config_file: str,
    input_suffix: str,
    output_suffix: str,
) -> None:
    """Batch-transform camera poses to vehicle reference-point poses."""
    dispatch_transform_camera_poses_batch(
        input_dir, output_dir, vehicle_config_file, input_suffix, output_suffix
    )


@renav_group.command()
@click.option(
    "--target-dir",
    "target_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory containing target camera pose CSV files",
)
@click.option(
    "--source-dir",
    "source_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory containing source camera pose CSV files",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write corrected CSV files into",
)
@click.option(
    "--target-suffix",
    "target_suffix",
    type=str,
    default="_renav_stereo_poses.csv",
    show_default=True,
    help="suffix stripped from target filenames to derive the deployment label",
)
@click.option(
    "--source-suffix",
    "source_suffix",
    type=str,
    default="_cameras.csv",
    show_default=True,
    help="suffix appended to the deployment label to find the source file",
)
def batch_correct_poses(
    target_dir: str,
    source_dir: str,
    output_dir: str,
    target_suffix: str,
    source_suffix: str,
) -> None:
    """Batch-correct Renav camera poses with source camera pose latitude/longitude."""
    dispatch_batch_correct_renav_poses(
        target_dir,
        source_dir,
        output_dir,
        target_suffix,
        source_suffix,
    )
