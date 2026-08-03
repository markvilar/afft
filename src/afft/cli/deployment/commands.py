"""CLI commands for working with ACFR deployments."""

import click

from afft.deployment import EnrichmentSection

from .actions import (
    dispatch_describe_deployment,
    dispatch_enrich_descriptor,
    dispatch_scaffold_catalog,
    dispatch_summarize_catalog,
    dispatch_summarize_descriptor,
)


@click.group()
@click.pass_context
def deployment_group(context: click.Context) -> None:
    """CLI group for deployment commands."""
    context.ensure_object(dict)


@deployment_group.command()
@click.option(
    "--input",
    "root_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="root directory containing ACFR deployment subdirectories",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the deployment descriptors as TOML",
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
    "--verbose",
    is_flag=True,
    default=False,
    help="log diagnostics warnings after the run completes",
)
def describe(
    root_dir: str,
    output_file: str,
    deployment_suffix: str,
    verbose: bool,
) -> None:
    """Describe the deployments in an ACFR deployment data directory tree."""
    dispatch_describe_deployment(
        root_dir, output_file, deployment_suffix, verbose
    )


@deployment_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment descriptors TOML file",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the deployment catalog skeleton as TOML",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log diagnostics warnings after the run completes",
)
def scaffold_catalog(
    input_file: str,
    output_file: str,
    verbose: bool,
) -> None:
    """Scaffold a curated deployment catalog from deployment descriptors.

    The skeleton accounts for every deployment, but the curated fields —
    vessel names, sensor vendors and products, and every mounting pose — are
    left empty to be filled in by hand.
    """
    dispatch_scaffold_catalog(input_file, output_file, verbose)


@deployment_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment descriptors TOML file",
)
@click.option(
    "--catalog",
    "catalog_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the curated deployment catalog TOML file",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the enriched descriptors as TOML",
)
@click.option(
    "--section",
    type=click.Choice([section.value for section in EnrichmentSection]),
    default=EnrichmentSection.ALL.value,
    show_default=True,
    help="descriptor sections to fill from the catalog",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log diagnostics warnings after the run completes",
)
def enrich(
    input_file: str,
    catalog_file: str,
    output_file: str,
    section: str,
    verbose: bool,
) -> None:
    """Enrich deployment descriptors from a curated deployment catalog.

    Fills the curated slots the deployment data files cannot supply — platform
    and vessel identities, sensor identities, and mounting poses. Passing the
    input path as the output enriches the descriptors in place.
    """
    dispatch_enrich_descriptor(
        input_file, catalog_file, output_file, section, verbose
    )


@deployment_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the deployment descriptors TOML file",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    default=None,
    help="path to write a detailed Markdown report; omit to print a summary",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="list the deployments affected by each curation gap",
)
def summarize(
    input_file: str,
    output_file: str | None,
    verbose: bool,
) -> None:
    """Summarize the deployments in a deployment descriptors file.

    Without an output path, prints per-file aggregates to the terminal. With
    one, writes a detailed per-deployment report as Markdown.
    """
    dispatch_summarize_descriptor(input_file, output_file, verbose)


@deployment_group.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the curated deployment catalog TOML file",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="list the records affected by each curation gap",
)
def summarize_catalog(
    input_file: str,
    verbose: bool,
) -> None:
    """Summarize a curated deployment catalog.

    Prints curation progress to the terminal — record counts, profile
    assignment coverage, records nothing references, and the curated fields
    still left empty.
    """
    dispatch_summarize_catalog(input_file, verbose)
