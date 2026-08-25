"""Orchestrator for the collect Squidle+ media task."""

from pathlib import Path

from afft.deployment import DeploymentDescriptor, read_deployment_descriptors
from afft.squidle import create_client
from afft.utils.log import logger

from .image_downloader import build_download_plan, download_deployment_images
from .media_retriever import retrieve_deployment_media
from .report import build_run_report, write_run_report
from .types import (
    CollectSquidleMediaCommand,
    CollectSquidleMediaConfig,
    DeploymentImagesDownload,
    DeploymentState,
    DownloadSummary,
    MatchSummary,
    RetrievalSummary,
    RunReport,
    TaskState,
)


type Summary = MatchSummary | RetrievalSummary | DownloadSummary


def _validate_inputs(command: CollectSquidleMediaCommand) -> None:
    """Raise if the deployments file or output directory is missing."""
    if not command.deployments_file.exists():
        raise FileNotFoundError(
            f"deployments file not found: {command.deployments_file}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory not found: {command.output_dir}"
        )


def _log_run_header(command: CollectSquidleMediaCommand) -> None:
    """Log a banner describing the run."""
    logger.info("-------------------------------------")
    logger.info("Collect Squidle+ Media")
    logger.info(f"  deployments file: {command.deployments_file}")
    logger.info(f"  output dir:       {command.output_dir}")
    logger.info(f"  download images:  {command.download_images}")
    logger.info("-------------------------------------")


def summarize_matching(state: TaskState) -> MatchSummary:
    """Derive the phase 1 (matching) summary from the task state."""
    return MatchSummary(
        loaded=len(state.deployments),
        matched=len(state.matched),
        unmatched=[
            entry.deployment_info.metadata.acfr_deployment_label
            for entry in state.unmatched
        ],
    )


def summarize_retrieval(
    command: CollectSquidleMediaCommand,
    state: TaskState,
) -> RetrievalSummary:
    """Derive the phase 2 (retrieval) summary from the task state."""
    matched = state.matched
    exported: list[Path] = [
        command.output_dir
        / f"{entry.deployment_info.deployment_label}_media_records.csv"
        for entry in matched
        if entry.result is not None
    ]
    failed: list[str] = [
        entry.deployment_info.metadata.acfr_deployment_label
        for entry in matched
        if entry.failed
    ]
    return RetrievalSummary(
        attempted=len(matched), exported=exported, failed=failed
    )


def summarize_download(state: TaskState) -> DownloadSummary:
    """Derive the phase 3 (download) summary from the task state."""
    downloads = [
        entry.downloads
        for entry in state.matched
        if entry.downloads is not None
    ]
    return DownloadSummary(
        deployments=len(downloads),
        downloaded=sum(len(d.downloaded) for d in downloads),
        skipped=sum(len(d.skipped) for d in downloads),
        failed=sum(len(d.failed) for d in downloads),
    )


def log_summary(summary: Summary) -> None:
    """Log a phase summary."""
    match summary:
        case MatchSummary():
            logger.info(
                f"matched {summary.matched}/{summary.loaded} deployment(s), "
                f"{len(summary.unmatched)} unmatched"
            )
            for label in summary.unmatched:
                logger.warning(f"  no Squidle+ match: {label!r}")
        case RetrievalSummary():
            logger.info(
                f"retrieved media for {len(summary.exported)}/"
                f"{summary.attempted} matched deployment(s), "
                f"{len(summary.failed)} failed"
            )
            for label in summary.failed:
                logger.warning(f"  retrieval failed: {label!r}")
        case DownloadSummary():
            logger.info(
                f"downloaded {summary.downloaded} image(s) across "
                f"{summary.deployments} deployment(s) "
                f"({summary.skipped} skipped, {summary.failed} failed)"
            )


def run_collect_squidle_media(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
) -> None:
    """
    Orchestrate the collect Squidle+ media task.

    Phases
    ------
    1. Load ACFR deployments and match them to Squidle+ deployments.
    2. Retrieve media records for each matched deployment.
    3. Optionally download the image files for the retrieved media.

    Arguments
    ---------
    command: Task command.
    config: Task configuration (carries the Squidle+ API token).

    Raises
    ------
    FileNotFoundError: If the deployments file or output directory is missing.
    """
    _validate_inputs(command)
    _log_run_header(command)

    with create_client(config.squidle_token.get_secret_value()) as client:
        # Phase 1 — load descriptors; matching is pre-resolved on
        # descriptor.squidle by `deployment enrich-squidle`.
        descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
            command.deployments_file
        )
        state: TaskState = TaskState(
            deployments=[
                DeploymentState(deployment_info=descriptor)
                for descriptor in descriptors
            ]
        )
        log_summary(summarize_matching(state))

        if command.dry_run:
            return

        # Phase 2 — retrieve media records
        retrieve_deployment_media(command, client, state)
        log_summary(summarize_retrieval(command, state))

        # Build image download plan (attaches to state; used by the report)
        downloads: list[DeploymentImagesDownload] = build_download_plan(
            command, state
        )

        # Phase 3 — download image files (optional)
        if command.download_images:
            download_deployment_images(downloads, command.max_workers)
            log_summary(summarize_download(state))

        # Build and write the run report
        report: RunReport = build_run_report(command, state)
        write_run_report(report, command.output_dir / "run_report.json")
