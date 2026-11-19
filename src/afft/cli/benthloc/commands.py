"""CLI commands for building Benthloc ingestion documents."""

import click

from .actions import (
    invoke_build_telemetry_ingestion_document,
    invoke_build_trajectory_ingestion_document,
)


@click.group()
@click.pass_context
def benthloc_group(context: click.Context) -> None:
    """CLI group for building Benthloc ingestion documents."""
    context.ensure_object(dict)


@benthloc_group.command("build-trajectory-ingestion-document")
@click.option(
    "--bundle",
    "bundle_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the processed deployment bundle to read from, never written",
)
@click.option(
    "--key",
    required=True,
    help="bundle key of the trajectory geoframe to read",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the Benthloc trajectory ingestion document to",
)
@click.option(
    "--trajectory-label",
    required=True,
    help="trajectory label, single-valued across the output file",
)
@click.option(
    "--trajectory-description",
    default=None,
    help="optional trajectory description",
)
@click.option(
    "--timestamp-column",
    default="timestamp",
    show_default=True,
    help="datetime column on the source geoframe",
)
@click.option(
    "--yaw-column",
    default="yaw",
    show_default=True,
    help="yaw (heading) column on the source geoframe, degrees",
)
@click.option(
    "--pitch-column",
    default="pitch",
    show_default=True,
    help="pitch column on the source geoframe, degrees",
)
@click.option(
    "--roll-column",
    default="roll",
    show_default=True,
    help="roll column on the source geoframe, degrees",
)
@click.option(
    "--platform-label",
    default=None,
    help="platform label override; falls back to the bundle's platform/identity",
)
@click.option(
    "--deployment-label",
    default=None,
    help="deployment label override; falls back to the bundle's deployment/identity",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="validate and report the labels and pose count without writing",
)
def build_trajectory_ingestion_document(
    bundle_file: str,
    key: str,
    output_file: str,
    trajectory_label: str,
    trajectory_description: str | None,
    timestamp_column: str,
    yaw_column: str,
    pitch_column: str,
    roll_column: str,
    platform_label: str | None,
    deployment_label: str | None,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Build a Benthloc trajectory ingestion document from a processed
    deployment bundle's trajectory geoframe."""
    invoke_build_trajectory_ingestion_document(
        bundle_file,
        key,
        output_file,
        trajectory_label,
        trajectory_description,
        timestamp_column,
        yaw_column,
        pitch_column,
        roll_column,
        platform_label,
        deployment_label,
        overwrite,
        dry_run,
    )


@benthloc_group.command("build-telemetry-ingestion-document")
@click.option(
    "--bundle",
    "bundle_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the built deployment bundle to read from, never written",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the task config TOML file holding the builder's section",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the Benthloc telemetry ingestion document to",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="validate and report the keys the document asserts without writing",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log accumulated diagnostics after the run completes",
)
def build_telemetry_ingestion_document(
    bundle_file: str,
    config_file: str,
    output_file: str,
    overwrite: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Build a Benthloc telemetry ingestion document from a built deployment
    bundle."""
    invoke_build_telemetry_ingestion_document(
        bundle_file,
        config_file,
        output_file,
        overwrite,
        dry_run,
        verbose,
    )
