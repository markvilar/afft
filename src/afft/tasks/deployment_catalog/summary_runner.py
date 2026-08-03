"""Runner for the summarize catalog task."""

from rich.console import Console
from rich.table import Table

from afft.deployment import (
    CatalogSummary,
    DeploymentCatalog,
    ProfileAssignment,
    read_deployment_catalog,
    summarize_catalog,
)
from afft.utils.log import logger

from .summary_types import SummarizeCatalogCommand, SummarizeCatalogResult


def _assignment_table(
    title: str,
    assignments: list[ProfileAssignment],
) -> Table:
    """Build a table of profiles and their assignment counts."""
    table = Table(title=title, title_justify="left")
    table.add_column("Profile")
    table.add_column("Deployments", justify="right")
    for assignment in assignments:
        table.add_row(assignment.profile_key, str(assignment.count))
    return table


def log_summary(summary: CatalogSummary, verbose: bool) -> None:
    """
    Print the brief catalog summary to the terminal.

    Arguments
    ---------
    summary: The computed summary.
    verbose: List the offending profile and deployment keys for each gap.
    """
    console = Console()
    coverage = summary.coverage

    records = Table(title="Records", title_justify="left", show_header=False)
    records.add_column("Table")
    records.add_column("Count", justify="right")
    records.add_row("Sensor identities", str(summary.sensor_identity_count))
    records.add_row("Platform profiles", str(summary.platform_profile_count))
    records.add_row("Vessel profiles", str(summary.vessel_profile_count))
    console.print(records)

    assignment = Table(
        title="Assignment coverage", title_justify="left", show_header=False
    )
    assignment.add_column("Field")
    assignment.add_column("Count", justify="right")
    assignment.add_row("Deployments", str(coverage.deployment_count))
    assignment.add_row("With platform", str(coverage.with_platform))
    assignment.add_row("With vessel", str(coverage.with_vessel))
    assignment.add_row("Platform only", str(len(coverage.platform_only)))
    assignment.add_row("Vessel only", str(len(coverage.vessel_only)))
    console.print(assignment)

    if verbose:
        for label, labels in (
            ("Platform only", coverage.platform_only),
            ("Vessel only", coverage.vessel_only),
        ):
            if labels:
                console.print(f"{label}:")
                for deployment_label in labels:
                    console.print(f"  {deployment_label}")

    console.print(
        _assignment_table("Platform profiles", summary.platform_assignments)
    )
    console.print(
        _assignment_table("Vessel profiles", summary.vessel_assignments)
    )

    if summary.unreferenced_sensors:
        console.print(
            f"{len(summary.unreferenced_sensors)} sensor identity(s) "
            "referenced by no profile:"
        )
        for sensor_key in summary.unreferenced_sensors:
            console.print(f"  {sensor_key}")

    if not summary.curation_gaps:
        console.print("No unfilled curated slots.")
        return

    gaps = Table(title="Curation gaps", title_justify="left")
    gaps.add_column("Field")
    gaps.add_column("Records", justify="right")
    for gap in summary.curation_gaps:
        gaps.add_row(gap.field_name, str(gap.count))
    console.print(gaps)

    if verbose:
        for gap in summary.curation_gaps:
            console.print(f"{gap.field_name}:")
            for record_key in gap.record_keys:
                console.print(f"  {record_key}")


def run_summarize_catalog(
    command: SummarizeCatalogCommand,
) -> SummarizeCatalogResult:
    """
    Summarize a curated deployment catalog, printing the aggregates to the
    terminal.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The computed summary.

    Raises
    ------
    FileNotFoundError: If the input file is missing.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )

    logger.info("-------------------------------------")
    logger.info("Summarize Deployment Catalog")
    logger.info(f"  input file: {command.input_file}")
    logger.info(f"  verbose:    {command.verbose}")
    logger.info("-------------------------------------")

    catalog: DeploymentCatalog = read_deployment_catalog(command.input_file)
    summary: CatalogSummary = summarize_catalog(catalog)

    log_summary(summary, command.verbose)

    return SummarizeCatalogResult(summary=summary)
