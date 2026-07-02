"""Build and export the run report for the collect Squidle+ media task."""

import msgspec

from pathlib import Path
from typing import Any

from afft.squidle import Deployment

from .types import (
    CollectSquidleMediaCommand,
    DeploymentReport,
    DeploymentState,
    DownloadReport,
    RunReport,
    TaskState,
)


def build_run_report(
    command: CollectSquidleMediaCommand,
    state: TaskState,
) -> RunReport:
    """
    Build the run report from the accumulated task state.

    Arguments
    ---------
    command: Task command.
    state: Task state after all phases have run.

    Returns
    -------
    A RunReport with one DeploymentReport per ACFR deployment.
    """
    return RunReport(
        deployments_file=str(command.deployments_file),
        output_dir=str(command.output_dir),
        deployments=[
            _build_deployment_report(command, entry)
            for entry in state.deployments
        ],
    )


def _build_deployment_report(
    command: CollectSquidleMediaCommand,
    entry: DeploymentState,
) -> DeploymentReport:
    """Build the report for a single deployment from its state."""
    metadata = entry.deployment_info.metadata
    deployment: Deployment | None = entry.squidle_deployment
    label: str = entry.deployment_info.deployment_label
    media_records_file: str | None = (
        str(command.output_dir / f"{label}_media_records.csv")
        if entry.result is not None
        else None
    )
    download: DownloadReport | None = (
        DownloadReport(images=entry.downloads.images)
        if entry.downloads is not None
        else None
    )
    return DeploymentReport(
        acfr_deployment_label=metadata.acfr_deployment_label,
        acfr_campaign_label=metadata.acfr_campaign_label,
        matched=entry.matched,
        squidle_deployment_id=deployment.id if deployment else None,
        squidle_deployment_key=deployment.key if deployment else None,
        squidle_deployment_name=deployment.name if deployment else None,
        squidle_campaign_name=deployment.campaign_name if deployment else None,
        squidle_platform_name=deployment.platform_name if deployment else None,
        media_records_file=media_records_file,
        media_record_count=len(entry.media) if entry.media else 0,
        retrieval_error=entry.error,
        download=download,
    )


def write_run_report(report: RunReport, output_file: Path) -> None:
    """
    Serialize the run report to a JSON file.

    Arguments
    ---------
    report: The run report to write.
    output_file: Destination JSON path.
    """
    encoded: bytes = msgspec.json.encode(_report_to_dict(report))
    output_file.write_bytes(msgspec.json.format(encoded, indent=2))


def _report_to_dict(report: RunReport) -> dict[str, Any]:
    return {
        "deployments_file": report.deployments_file,
        "output_dir": report.output_dir,
        "deployments": [
            _deployment_to_dict(deployment) for deployment in report.deployments
        ],
    }


def _deployment_to_dict(report: DeploymentReport) -> dict[str, Any]:
    return {
        "acfr_deployment_label": report.acfr_deployment_label,
        "acfr_campaign_label": report.acfr_campaign_label,
        "matched": report.matched,
        "squidle_deployment_id": report.squidle_deployment_id,
        "squidle_deployment_key": report.squidle_deployment_key,
        "squidle_deployment_name": report.squidle_deployment_name,
        "squidle_campaign_name": report.squidle_campaign_name,
        "squidle_platform_name": report.squidle_platform_name,
        "media_records_file": report.media_records_file,
        "media_record_count": report.media_record_count,
        "retrieval_error": report.retrieval_error,
        "download": (
            _download_to_dict(report.download)
            if report.download is not None
            else None
        ),
    }


def _download_to_dict(report: DownloadReport) -> dict[str, Any]:
    return {
        "downloaded": report.downloaded,
        "skipped": report.skipped,
        "failed": report.failed,
        "failures": [
            {
                "source": image.source,
                "destination": str(image.destination),
                "error": image.error,
            }
            for image in report.failures
        ],
    }
