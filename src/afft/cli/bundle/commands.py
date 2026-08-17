"""CLI commands for working with deployment bundles."""

from datetime import datetime

import click

from .actions import (
    invoke_build_deployment_bundle,
    invoke_clip_deployment_bundle,
    invoke_export_bundle_frame,
    invoke_ingest_bundle_frame,
    invoke_list_deployment_bundle,
    invoke_process_deployment_bundle,
)


class IsoDateTime(click.ParamType[datetime]):
    """A datetime parsed from ISO8601, rather than from a fixed format list.

    `click.DateTime` matches against a list of formats and none of its
    defaults carries a UTC offset, so an offset-bearing bound would be
    rejected. Whether the parsed value is naive is left to the task, which
    takes a naive bound as UTC.
    """

    name: str = "iso8601"

    def convert(
        self,
        value: object,
        param: click.Parameter | None,
        context: click.Context | None,
    ) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            self.fail(f"{value!r} is not an ISO8601 datetime", param, context)


@click.group()
@click.pass_context
def bundle_group(context: click.Context) -> None:
    """CLI group for deployment bundle commands."""
    context.ensure_object(dict)


@bundle_group.command()
@click.option(
    "--descriptor-file",
    "descriptor_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment descriptors TOML file",
)
@click.option(
    "--deployment-label",
    "deployment_label",
    type=str,
    required=True,
    help="label of the deployment to build, selected from --descriptor-file",
)
@click.option(
    "--data-dir",
    "data_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="per-deployment data directory",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the shared task config TOML file",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the deployment bundle to",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log diagnostics warnings after the run completes",
)
def build(
    descriptor_file: str,
    deployment_label: str,
    data_dir: str,
    config_file: str,
    output_file: str,
    overwrite: bool,
    verbose: bool,
) -> None:
    """Build a deployment bundle from a descriptor and its raw message logs."""
    invoke_build_deployment_bundle(
        descriptor_file,
        deployment_label,
        data_dir,
        config_file,
        output_file,
        overwrite,
        verbose,
    )


@bundle_group.command("list")
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment bundle to list",
)
@click.option(
    "--dtypes",
    is_flag=True,
    default=False,
    help="also list each frame's recorded column dtypes",
)
def list_contents(input_file: str, dtypes: bool) -> None:
    """List the frames a deployment bundle holds."""
    invoke_list_deployment_bundle(input_file, dtypes)


@bundle_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment bundle to process",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the shared task config TOML file",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the processed deployment bundle to",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log each step's output key as it is written",
)
def process(
    input_file: str,
    config_file: str,
    output_file: str,
    overwrite: bool,
    verbose: bool,
) -> None:
    """Run the configured processing pipeline over a deployment bundle."""
    invoke_process_deployment_bundle(
        input_file,
        config_file,
        output_file,
        overwrite,
        verbose,
    )


@bundle_group.command("ingest-frame")
@click.option(
    "--bundle",
    "bundle_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment bundle to ingest into, written in place",
)
@click.option(
    "--key",
    required=True,
    help="bundle key to write the frame to",
)
@click.option(
    "--file",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the CSV or geodata file holding the frame",
)
@click.option(
    "--datetime-column",
    "datetime_columns",
    multiple=True,
    help="column to parse as a timezone-aware UTC timestamp; repeatable",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite an existing frame at the key",
)
def ingest_frame(
    bundle_file: str,
    key: str,
    input_file: str,
    datetime_columns: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Ingest a frame from a file into an existing deployment bundle."""
    invoke_ingest_bundle_frame(
        bundle_file,
        key,
        input_file,
        datetime_columns,
        overwrite,
    )


@bundle_group.command("export-frame")
@click.option(
    "--bundle",
    "bundle_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment bundle to export from, never written",
)
@click.option(
    "--key",
    required=True,
    help="bundle key to read the frame from",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the frame to; its suffix selects the format",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
def export_frame(
    bundle_file: str,
    key: str,
    output_file: str,
    overwrite: bool,
) -> None:
    """Export a single frame from a deployment bundle to a file."""
    invoke_export_bundle_frame(
        bundle_file,
        key,
        output_file,
        overwrite,
    )


@bundle_group.command("clip")
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment bundle to clip, never written",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the clipped bundle to",
)
@click.option(
    "--start",
    type=IsoDateTime(),
    required=True,
    help="start of the clip window, inclusive; naive values are taken as UTC",
)
@click.option(
    "--end",
    type=IsoDateTime(),
    required=True,
    help="end of the clip window, inclusive; naive values are taken as UTC",
)
@click.option(
    "--label-suffix",
    required=True,
    help="suffix joined onto the source deployment label with an underscore",
)
@click.option(
    "--datetime-column",
    default="timestamp",
    show_default=True,
    help="column to clip on; frames without it are copied whole",
)
@click.option(
    "--no-clip",
    "no_clip_patterns",
    multiple=True,
    help="key pattern whose frames are copied whole; repeatable",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite the output file if it already exists",
)
def clip(
    input_file: str,
    output_file: str,
    start: datetime,
    end: datetime,
    label_suffix: str,
    datetime_column: str,
    no_clip_patterns: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Clip a deployment bundle's tables to a temporal window."""
    invoke_clip_deployment_bundle(
        input_file,
        output_file,
        start,
        end,
        label_suffix,
        datetime_column,
        no_clip_patterns,
        overwrite,
    )
