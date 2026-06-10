"""Runner for the collect Squidle+ media task."""

from pathlib import Path
from typing import Any

import pandas as pd

from afft.io.config_io import read_config
from afft.squidle import (
    SquidleClient,
    create_client,
    fetch_deployments,
    fetch_media,
    fetch_platforms,
)
from afft.squidle.types import Deployment
from afft.tasks.collect_deployment_info import (
    DeploymentInfo,
    DeploymentMetadata,
)
from afft.utils.log import logger

from .types import (
    CollectSquidleMediaCommand,
    CollectSquidleMediaConfig,
    CollectSquidleMediaContext,
    CollectSquidleMediaResult,
    DeploymentKeyResolver,
    DeploymentLookupBuilder,
    DeploymentMatchPolicy,
    DeploymentMatcher,
    DeploymentMediaContext,
)


def load_acfr_deployments(
    command: CollectSquidleMediaCommand,
) -> list[DeploymentInfo]:
    """
    Load ACFR deployment entries from the deployments TOML file.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    List of deployment info objects.
    """
    raw: dict[str, Any] = read_config(command.deployments_file)
    deployments: list[DeploymentInfo] = []
    for entry in raw.get("deployments", []):
        metadata: dict[str, Any] = entry.get("metadata", {})
        deployments.append(
            DeploymentInfo(
                deployment_label=entry["deployment_label"],
                deployment_datetime=entry["deployment_datetime"],
                deployment_platform=entry.get("deployment_platform", ""),
                metadata=DeploymentMetadata(
                    acfr_deployment_label=metadata["acfr_deployment_label"],
                    acfr_campaign_label=metadata["acfr_campaign_label"],
                    acfr_platform_label=metadata.get("acfr_platform_label", ""),
                    origin_latitude=metadata.get("origin_latitude", 0.0),
                    origin_longitude=metadata.get("origin_longitude", 0.0),
                    magnetic_variation=metadata.get("magnetic_variation", 0.0),
                    message_topics=metadata.get("message_topics", []),
                    renav_labels=metadata.get("renav_labels", []),
                    camera_calibration_files=metadata.get(
                        "camera_calibration_files", []
                    ),
                ),
            )
        )
    return deployments


def _squidle_datetime_key(key: str) -> str:
    """
    Extract ``{YYYYMMDD}_{HHMMSS}`` from a Squidle+ deployment key.

    Squidle+ keys follow the format ``r{YYYYMMDD}_{HHMMSS}_{name}``.
    """
    parts: list[str] = key.split("_", 2)
    return f"{parts[0][1:]}_{parts[1]}"


def _acfr_datetime_key(deployment_label: str) -> str:
    """
    Extract ``{YYYYMMDD}_{HHMMSS}`` from an ACFR deployment label.

    ACFR deployment labels follow the format ``{geohash}_{YYYYMMDD}_{HHMMSS}``.
    """
    parts: list[str] = deployment_label.rsplit("_", 2)
    return f"{parts[-2]}_{parts[-1]}"


def create_deployment_matcher(
    policy: DeploymentMatchPolicy,
) -> DeploymentMatcher:
    """
    Create a deployment matcher for the given match policy.

    Returns a callable that takes a list of Squidle+ deployments and builds
    a lookup, and a second callable that resolves the lookup key for an
    ACFR deployment context.

    Arguments
    ---------
    policy: Strategy for matching ACFR deployments to Squidle+ deployments.

    Returns
    -------
    Tuple of ``(build_lookup, resolve_key)`` callables.
    """
    if policy == DeploymentMatchPolicy.BY_NAME:

        def build_lookup(
            deployments: list[Deployment],
        ) -> dict[str, Deployment]:
            return {deployment.name: deployment for deployment in deployments}

        def resolve_key(context: DeploymentMediaContext) -> str:
            return context.acfr_deployment.metadata.acfr_deployment_label

    else:

        def build_lookup(
            deployments: list[Deployment],
        ) -> dict[str, Deployment]:
            return {
                _squidle_datetime_key(deployment.key): deployment
                for deployment in deployments
            }

        def resolve_key(context: DeploymentMediaContext) -> str:
            return _acfr_datetime_key(context.acfr_deployment.deployment_label)

    return build_lookup, resolve_key


def match_deployment(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
    context: DeploymentMediaContext,
    squidle_lookup: dict[str, Deployment],
    resolve_key: DeploymentKeyResolver,
) -> DeploymentMediaContext:
    """
    Match the ACFR deployment to a Squidle+ deployment.

    Uses ``resolve_key`` to derive the lookup key from the context, then
    looks it up in ``squidle_lookup``. Logs a warning and leaves
    ``squidle_deployment`` as ``None`` if no match is found.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.
    context: Per-deployment context.
    squidle_lookup: Mapping from match key to Squidle+ deployment.
    resolve_key: Callable that extracts the match key from a context.

    Returns
    -------
    Updated context with ``squidle_deployment`` set if a match was found.
    """
    acfr_label: str = context.acfr_deployment.metadata.acfr_deployment_label
    lookup_key: str = resolve_key(context)
    match: Deployment | None = squidle_lookup.get(lookup_key)
    if match is None:
        logger.warning(
            f"no Squidle+ deployment match for: {acfr_label!r} "
            f"(policy={command.match_policy.value}, key={lookup_key!r})"
        )
        return context
    context.squidle_deployment = match
    return context


def fetch_media_items(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
    context: DeploymentMediaContext,
    client: SquidleClient,
) -> DeploymentMediaContext:
    """
    Fetch media items from Squidle+ for the matched deployment.

    Skipped if ``squidle_deployment`` is not set.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.
    context: Per-deployment context.
    client: Authenticated Squidle+ client.

    Returns
    -------
    Updated context with ``media`` set.
    """
    if context.squidle_deployment is None:
        return context
    context.media = fetch_media(client, context.squidle_deployment.id)
    return context


def format_result(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
    context: DeploymentMediaContext,
) -> DeploymentMediaContext:
    """
    Annotate the media DataFrame with ACFR and Squidle+ identity columns.

    Skipped if ``squidle_deployment`` or ``media`` is not set.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.
    context: Per-deployment context.

    Returns
    -------
    Updated context with ``result`` set.
    """
    if context.squidle_deployment is None or context.media is None:
        return context
    deployment: Deployment = context.squidle_deployment
    result: pd.DataFrame = context.media.copy()
    result["acfr_deployment_label"] = (
        context.acfr_deployment.metadata.acfr_deployment_label
    )
    result["acfr_campaign_label"] = (
        context.acfr_deployment.metadata.acfr_campaign_label
    )
    result["squidle_deployment_id"] = deployment.id
    result["squidle_deployment_key"] = deployment.key
    result["squidle_deployment_name"] = deployment.name
    result["squidle_campaign_id"] = deployment.campaign_id
    result["squidle_campaign_name"] = deployment.campaign_name
    result["squidle_platform_id"] = deployment.platform_id
    result["squidle_platform_name"] = deployment.platform_name
    context.result = result
    return context


def export_result(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
    context: DeploymentMediaContext,
) -> DeploymentMediaContext:
    """
    Write the annotated media DataFrame to a CSV file.

    Skipped if ``result`` is not set. The output filename is derived from
    ``acfr_deployment_label``.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.
    context: Per-deployment context.

    Returns
    -------
    Unchanged context.
    """
    if context.result is None:
        return context
    deployment_label: str = context.acfr_deployment.deployment_label
    acfr_label: str = context.acfr_deployment.metadata.acfr_deployment_label
    output_file: Path = (
        command.output_dir / f"{deployment_label}_squidle_media.csv"
    )
    context.result.to_csv(output_file, index=False)
    logger.info(
        f"{acfr_label}: {len(context.result)} record(s) → {output_file.name}"
    )
    return context


def run_collect_squidle_media(
    command: CollectSquidleMediaCommand,
    config: CollectSquidleMediaConfig,
) -> CollectSquidleMediaResult:
    """
    Collect Squidle+ media for all deployments in the ACFR deployments file.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.

    Returns
    -------
    Result with paths of exported CSVs and labels of skipped deployments.

    Raises
    ------
    FileNotFoundError: If the deployments file or output directory does not exist.
    """
    if not command.deployments_file.exists():
        raise FileNotFoundError(
            f"deployments file not found: {command.deployments_file}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory not found: {command.output_dir}"
        )

    logger.info("-------------------------------------")
    logger.info("Collect Squidle+ Media")
    logger.info(f"  deployments file: {command.deployments_file}")
    logger.info(f"  output dir:       {command.output_dir}")
    logger.info("-------------------------------------")

    acfr_deployments: list[DeploymentInfo] = load_acfr_deployments(command)
    logger.info(f"loaded {len(acfr_deployments)} ACFR deployment(s)")

    build_lookup: DeploymentLookupBuilder
    resolve_key: DeploymentKeyResolver
    build_lookup, resolve_key = create_deployment_matcher(command.match_policy)
    logger.info(f"match policy: {command.match_policy.value}")

    task_context: CollectSquidleMediaContext = CollectSquidleMediaContext(
        deployments=[
            DeploymentMediaContext(acfr_deployment=deployment)
            for deployment in acfr_deployments
        ]
    )

    with create_client() as client:
        squidle_lookup: dict[str, Deployment] = {}
        platform_names: set[str] = {
            context.acfr_deployment.deployment_platform
            for context in task_context.deployments
            if context.acfr_deployment.deployment_platform
        }
        for platform_name in platform_names:
            platform_filters: list[dict[str, Any]] = [
                {"name": "name", "op": "eq", "val": platform_name}
            ]
            platforms = fetch_platforms(client, platform_filters)
            if not platforms:
                logger.warning(
                    f"no Squidle+ platform found with name: {platform_name!r}"
                )
                continue
            platform_id: int = platforms[0].id
            logger.info(
                f"resolved platform {platform_name!r} → id={platform_id}"
            )
            deployment_filters: list[dict[str, Any]] = [
                {"name": "platform_id", "op": "eq", "val": platform_id}
            ]
            platform_deployments: list[Deployment] = fetch_deployments(
                client, deployment_filters
            )
            squidle_lookup.update(build_lookup(platform_deployments))
            logger.info(
                f"fetched {len(platform_deployments)} deployment(s) "
                f"for platform {platform_name!r}"
            )

        for i, context in enumerate(task_context.deployments):
            context = match_deployment(
                command, config, context, squidle_lookup, resolve_key
            )
            context = fetch_media_items(command, config, context, client)
            context = format_result(command, config, context)
            context = export_result(command, config, context)
            task_context.deployments[i] = context

    exported: list[Path] = [
        command.output_dir
        / f"{ctx.acfr_deployment.deployment_label}_squidle_media.csv"
        for ctx in task_context.deployments
        if ctx.result is not None
    ]
    skipped: list[str] = [
        ctx.acfr_deployment.metadata.acfr_deployment_label
        for ctx in task_context.deployments
        if ctx.squidle_deployment is None
    ]

    if command.verbose:
        for label in skipped:
            logger.warning(f"skipped (no Squidle+ match): {label!r}")

    logger.info(
        f"exported {len(exported)} deployment(s), skipped {len(skipped)}"
    )
    return CollectSquidleMediaResult(exported=exported, skipped=skipped)
