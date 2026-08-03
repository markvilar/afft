"""Actions for deployment CLI commands."""

from pathlib import Path

from afft.deployment import EnrichmentSection
from afft.tasks.deployment_catalog import (
    ScaffoldCatalogCommand,
    SummarizeCatalogCommand,
    run_scaffold_catalog,
    run_summarize_catalog,
)
from afft.tasks.deployment_descriptor import (
    DescribeDeploymentCommand,
    DescribeDeploymentResult,
    SummarizeDescriptorCommand,
    run_describe_deployment,
    run_summarize_descriptor,
)
from afft.tasks.deployment_enrichment import (
    EnrichDescriptorCommand,
    run_enrich_descriptor,
)


def dispatch_describe_deployment(
    root_dir: str | Path,
    output_file: str | Path,
    deployment_suffix: str = "_deployment_data",
    verbose: bool = False,
) -> None:
    """
    Describe the deployments under an ACFR deployment data directory tree.

    Exits non-zero if any deployment was skipped, so a partial run is visible
    to the caller without discarding the deployments that succeeded.
    """
    command = DescribeDeploymentCommand(
        root_dir=Path(root_dir),
        output_file=Path(output_file),
        deployment_suffix=deployment_suffix,
        verbose=verbose,
    )
    result: DescribeDeploymentResult = run_describe_deployment(command)
    if result.diagnostics.failures:
        raise SystemExit(1)


def dispatch_scaffold_catalog(
    input_file: str | Path,
    output_file: str | Path,
    verbose: bool = False,
) -> None:
    """
    Scaffold a deployment catalog skeleton from a deployment descriptors file.
    """
    command = ScaffoldCatalogCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
        verbose=verbose,
    )
    run_scaffold_catalog(command)


def dispatch_enrich_descriptor(
    input_file: str | Path,
    catalog_file: str | Path,
    output_file: str | Path,
    section: str = EnrichmentSection.ALL,
    verbose: bool = False,
) -> None:
    """
    Enrich deployment descriptors from a curated deployment catalog.

    Exits zero whatever the diagnostics hold: a deployment the catalog assigns
    no profile keeps its unfilled slots rather than failing the run.
    """
    command = EnrichDescriptorCommand(
        input_file=Path(input_file),
        catalog_file=Path(catalog_file),
        output_file=Path(output_file),
        section=EnrichmentSection(section),
        verbose=verbose,
    )
    run_enrich_descriptor(command)


def dispatch_summarize_descriptor(
    input_file: str | Path,
    output_file: str | Path | None = None,
    verbose: bool = False,
) -> None:
    """
    Summarize the deployments in a deployment descriptors file.

    Always exits zero: unfilled curated slots are the summary's output, not a
    failure of the run.
    """
    command = SummarizeDescriptorCommand(
        input_file=Path(input_file),
        output_file=Path(output_file) if output_file else None,
        verbose=verbose,
    )
    run_summarize_descriptor(command)


def dispatch_summarize_catalog(
    input_file: str | Path,
    verbose: bool = False,
) -> None:
    """
    Summarize a curated deployment catalog.

    Always exits zero: curation gaps are the summary's output, not a failure of
    the run.
    """
    command = SummarizeCatalogCommand(
        input_file=Path(input_file), verbose=verbose
    )
    run_summarize_catalog(command)
