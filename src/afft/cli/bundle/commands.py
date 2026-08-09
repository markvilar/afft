"""CLI commands for working with deployment bundles."""

import click

from .actions import (
    dispatch_build_deployment_bundle,
    dispatch_process_deployment_bundle,
)


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
    dispatch_build_deployment_bundle(
        descriptor_file,
        deployment_label,
        data_dir,
        config_file,
        output_file,
        overwrite,
        verbose,
    )


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
    dispatch_process_deployment_bundle(
        input_file,
        config_file,
        output_file,
        overwrite,
        verbose,
    )
