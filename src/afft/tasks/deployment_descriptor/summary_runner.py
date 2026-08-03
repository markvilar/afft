"""Runner for the summarize descriptors task."""

from rich.console import Console
from rich.table import Table

from afft.deployment import (
    DeploymentDescriptor,
    DescriptorSummary,
    read_deployment_descriptors,
    summarize_descriptors,
    write_summary_report,
)
from afft.utils.log import logger

from .summary_types import (
    SummarizeDescriptorCommand,
    SummarizeDescriptorResult,
)


def _count_table(title: str, name_header: str, counts: dict[str, int]) -> Table:
    """Build a two-column table of names and counts."""
    table = Table(title=title, title_justify="left")
    table.add_column(name_header)
    table.add_column("Deployments", justify="right")
    for name, count in counts.items():
        table.add_row(name, str(count))
    return table


def log_summary(summary: DescriptorSummary, verbose: bool) -> None:
    """
    Print the brief per-file aggregate summary to the terminal.

    Arguments
    ---------
    summary: The computed summary.
    verbose: List the offending deployment labels for each curation gap.
    """
    console = Console()
    extent = summary.extent

    overview = Table(title="Overview", title_justify="left", show_header=False)
    overview.add_column("Field")
    overview.add_column("Value")
    overview.add_row("Deployments", str(summary.deployment_count))
    overview.add_row("Campaigns", str(len(summary.campaign_counts)))
    overview.add_row("Earliest", summary.earliest_datetime.isoformat())
    overview.add_row("Latest", summary.latest_datetime.isoformat())
    overview.add_row(
        "Latitude", f"{extent.min_latitude} to {extent.max_latitude}"
    )
    overview.add_row(
        "Longitude", f"{extent.min_longitude} to {extent.max_longitude}"
    )
    overview.add_row("Enriched", "yes" if summary.enriched else "no")
    console.print(overview)

    console.print(
        _count_table("Campaigns", "Campaign", summary.campaign_counts)
    )

    coverage = Table(title="File coverage", title_justify="left")
    coverage.add_column("Section")
    coverage.add_column("Deployments", justify="right")
    coverage.add_column("Missing", justify="right")
    for section, count in summary.section_coverage.items():
        coverage.add_row(
            section, str(count), str(summary.deployment_count - count)
        )
    console.print(coverage)

    console.print(
        _count_table("Telemetry topics", "Topic", summary.topic_counts)
    )

    if not summary.enriched:
        console.print(
            "The descriptors are not enriched, so every curated slot is "
            "unfilled."
        )
        return

    if not summary.curation_gaps:
        console.print("No unfilled curated slots.")
        return

    gaps = Table(title="Curation gaps", title_justify="left")
    gaps.add_column("Field")
    gaps.add_column("Deployments", justify="right")
    for gap in summary.curation_gaps:
        gaps.add_row(gap.field_name, str(gap.count))
    console.print(gaps)

    if verbose:
        for gap in summary.curation_gaps:
            console.print(f"{gap.field_name}:")
            for label in gap.deployment_labels:
                console.print(f"  {label}")


def run_summarize_descriptor(
    command: SummarizeDescriptorCommand,
) -> SummarizeDescriptorResult:
    """
    Summarize a deployment descriptor file, printing the aggregates or writing
    a detailed report.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The computed summary and the path written, if any.

    Raises
    ------
    FileNotFoundError: If the input file or the output directory is missing.
    ValueError: If the input file holds no deployments.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if command.output_file and not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    logger.info("-------------------------------------")
    logger.info("Summarize Deployment Descriptors")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  verbose:     {command.verbose}")
    logger.info("-------------------------------------")

    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        command.input_file
    )
    if not descriptors:
        raise ValueError(f"no deployments in {command.input_file}")

    summary: DescriptorSummary = summarize_descriptors(descriptors)

    if command.output_file:
        write_summary_report(command.output_file, summary)
        logger.info(
            f"wrote a report for {summary.deployment_count} deployment(s) "
            f"to {command.output_file}"
        )
    else:
        log_summary(summary, command.verbose)

    return SummarizeDescriptorResult(
        summary=summary, output_file=command.output_file
    )
