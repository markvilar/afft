"""Phase 2: retrieve, annotate, and export Squidle+ media records."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path

import pandas as pd

from rich.console import Console
from rich.progress import Progress, TaskID

from afft.squidle import Deployment, SquidleClient
from afft.utils.log import logger

from .types import CollectSquidleMediaCommand, DeploymentState, TaskState


type DeploymentStep = Callable[[DeploymentState], DeploymentState]


def fetch_media_items(
    client: SquidleClient,
    entry: DeploymentState,
) -> DeploymentState:
    """
    Fetch media records for the matched deployment (step 1).

    Skipped if unmatched. A terminal export failure is recorded on
    ``entry.error`` (warn-and-continue) rather than raised, so one bad
    deployment does not abort the run.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    entry: Per-deployment state.

    Returns
    -------
    The (mutated) entry.
    """
    if entry.squidle_deployment is None:
        return entry
    try:
        entry.media = client.fetch_media(entry.squidle_deployment.id)
    except Exception as error:  # isolate API/export failures per deployment
        entry.error = str(error)
        label: str = entry.deployment_info.metadata.acfr_deployment_label
        logger.warning(f"media retrieval failed for {label!r}: {error}")
    return entry


def annotate_media(entry: DeploymentState) -> DeploymentState:
    """
    Annotate the media records with ACFR/Squidle+ identity columns (step 2).

    Skipped if unmatched or no media was retrieved.

    Arguments
    ---------
    entry: Per-deployment state.

    Returns
    -------
    The (mutated) entry with ``result`` set.
    """
    if entry.squidle_deployment is None or entry.media is None:
        return entry
    deployment: Deployment = entry.squidle_deployment
    metadata = entry.deployment_info.metadata
    result: pd.DataFrame = pd.DataFrame(
        [record.to_dict() for record in entry.media]
    )
    result["acfr_deployment_label"] = metadata.acfr_deployment_label
    result["acfr_campaign_label"] = metadata.acfr_campaign_label
    result["squidle_deployment_id"] = deployment.id
    result["squidle_deployment_key"] = deployment.key
    result["squidle_deployment_name"] = deployment.name
    result["squidle_campaign_id"] = deployment.campaign_id
    result["squidle_campaign_name"] = deployment.campaign_name
    result["squidle_platform_id"] = deployment.platform_id
    result["squidle_platform_name"] = deployment.platform_name
    entry.result = result
    return entry


def export_media(
    command: CollectSquidleMediaCommand,
    entry: DeploymentState,
) -> DeploymentState:
    """
    Write the annotated media DataFrame to a CSV file (step 3).

    Skipped if no annotated result. The filename is
    ``{deployment_label}_media_records.csv``.

    Arguments
    ---------
    command: Task command.
    entry: Per-deployment state.

    Returns
    -------
    The (unchanged) entry.
    """
    if entry.result is None:
        return entry
    label: str = entry.deployment_info.deployment_label
    acfr_label: str = entry.deployment_info.metadata.acfr_deployment_label
    output_file: Path = command.output_dir / f"{label}_media_records.csv"
    entry.result.to_csv(output_file, index=False)
    logger.info(
        f"{acfr_label}: {len(entry.result)} record(s) → {output_file.name}"
    )
    return entry


def build_media_pipeline(
    command: CollectSquidleMediaCommand,
    client: SquidleClient,
) -> list[DeploymentStep]:
    """
    Build the per-deployment media step pipeline (fetch → annotate → export).

    Contextual arguments are bound up front so each step is ``(entry) -> entry``.

    Arguments
    ---------
    command: Task command.
    client: Authenticated Squidle+ client.

    Returns
    -------
    Ordered list of pipeline steps.
    """
    return [
        partial(fetch_media_items, client),
        annotate_media,
        partial(export_media, command),
    ]


def process_deployment(
    entry: DeploymentState,
    steps: list[DeploymentStep],
) -> DeploymentState:
    """Run one deployment through the media step pipeline."""
    for step in steps:
        entry = step(entry)
    return entry


def retrieve_deployment_media(
    command: CollectSquidleMediaCommand,
    client: SquidleClient,
    state: TaskState,
) -> None:
    """
    Retrieve, annotate, and export media for all matched deployments (phase 2).

    Runs the per-deployment pipeline concurrently, mutating each entry in
    place. A single progress bar advances as each deployment completes.

    Arguments
    ---------
    command: Task command.
    client: Authenticated Squidle+ client.
    state: Task state; only matched entries are processed.
    """
    steps: list[DeploymentStep] = build_media_pipeline(command, client)
    console: Console = Console()
    with Progress(
        console=console,
        transient=True,
        disable=not console.is_terminal,
    ) as progress:
        task: TaskID = progress.add_task(
            "Retrieving media", total=len(state.matched)
        )
        with ThreadPoolExecutor(max_workers=command.max_workers) as executor:
            futures: dict[Future[DeploymentState], DeploymentState] = {
                executor.submit(process_deployment, entry, steps): entry
                for entry in state.matched
            }
            for future in as_completed(futures):
                future.result()  # entry already mutated in place
                progress.advance(task)
