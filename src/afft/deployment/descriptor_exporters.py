"""Markdown export for deployment descriptor summaries."""

from pathlib import Path

from .descriptor_summary import DescriptorSummary

type MarkdownLines = list[str]


def format_table(headers: list[str], rows: list[list[str]]) -> MarkdownLines:
    """
    Format rows as a GitHub-flavoured Markdown pipe table.

    Arguments
    ---------
    headers: Column headers.
    rows: Row cells, one list per row.

    Returns
    -------
    The table lines, followed by a blank line.
    """
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
        "",
    ]


def format_overview(summary: DescriptorSummary) -> MarkdownLines:
    """Format the deployment count, datetime range, and extent."""
    extent = summary.extent
    return [
        "## Overview",
        "",
        f"- Deployments: {summary.deployment_count}",
        f"- Campaigns: {len(summary.campaign_counts)}",
        f"- Earliest: {summary.earliest_datetime.isoformat()}",
        f"- Latest: {summary.latest_datetime.isoformat()}",
        f"- Latitude: {extent.min_latitude} to {extent.max_latitude}",
        f"- Longitude: {extent.min_longitude} to {extent.max_longitude}",
        f"- Enriched: {'yes' if summary.enriched else 'no'}",
        "",
    ]


def format_campaigns(summary: DescriptorSummary) -> MarkdownLines:
    """Format the deployment count per campaign as a table."""
    return [
        "## Campaigns",
        "",
        *format_table(
            ["Campaign", "Deployments"],
            [
                [campaign, str(count)]
                for campaign, count in summary.campaign_counts.items()
            ],
        ),
    ]


def format_section_coverage(summary: DescriptorSummary) -> MarkdownLines:
    """Format file-section coverage as a table."""
    return [
        "## File coverage",
        "",
        *format_table(
            ["Section", "Deployments", "Missing"],
            [
                [
                    section,
                    str(count),
                    str(summary.deployment_count - count),
                ]
                for section, count in summary.section_coverage.items()
            ],
        ),
    ]


def format_topics(summary: DescriptorSummary) -> MarkdownLines:
    """Format telemetry topic frequency as a table."""
    return [
        "## Telemetry topics",
        "",
        *format_table(
            ["Topic", "Deployments"],
            [
                [topic, str(count)]
                for topic, count in summary.topic_counts.items()
            ],
        ),
    ]


def format_curation_gaps(summary: DescriptorSummary) -> MarkdownLines:
    """Format the unfilled curated slots, with the deployments affected."""
    if not summary.enriched:
        return [
            "## Curation gaps",
            "",
            "The descriptors are not enriched, so every curated slot is "
            "unfilled.",
            "",
        ]

    if not summary.curation_gaps:
        return ["## Curation gaps", "", "No unfilled curated slots.", ""]

    lines: MarkdownLines = ["## Curation gaps", ""]
    lines.extend(
        format_table(
            ["Field", "Deployments"],
            [
                [f"`{gap.field_name}`", str(gap.count)]
                for gap in summary.curation_gaps
            ],
        )
    )
    for gap in summary.curation_gaps:
        lines.extend(
            [
                f"### `{gap.field_name}`",
                "",
                *(f"- {label}" for label in gap.deployment_labels),
                "",
            ]
        )
    return lines


def format_deployments(summary: DescriptorSummary) -> MarkdownLines:
    """Format the per-deployment detail, one subsection per deployment."""
    lines: MarkdownLines = ["## Deployments", ""]
    for deployment in summary.deployments:
        files: str = ", ".join(
            f"{section} ({count})"
            for section, count in deployment.file_counts.items()
            if count > 0
        )
        lines.extend(
            [
                f"### {deployment.deployment_label}",
                "",
                f"- Datetime: {deployment.deployment_datetime.isoformat()}",
                f"- Campaign: {deployment.campaign_label}",
                f"- Files: {files if files else 'none'}",
                f"- Topics: {', '.join(deployment.topics) or 'none'}",
                "- Platform sensors: "
                f"{', '.join(deployment.platform_sensor_keys) or 'none'}",
                "- Vessel sensors: "
                f"{', '.join(deployment.vessel_sensor_keys) or 'none'}",
                f"- Unfilled slots: {len(deployment.unfilled_fields)}",
                "",
            ]
        )
    return lines


def write_summary_report(path: Path, summary: DescriptorSummary) -> None:
    """
    Write a detailed summary report as Markdown.

    Arguments
    ---------
    path: Path to write the report to.
    summary: The computed summary.
    """
    lines: MarkdownLines = [
        "# Deployment Descriptor Summary",
        "",
        *format_overview(summary),
        *format_campaigns(summary),
        *format_section_coverage(summary),
        *format_topics(summary),
        *format_curation_gaps(summary),
        *format_deployments(summary),
    ]
    path.write_text("\n".join(lines).rstrip("\n") + "\n")
