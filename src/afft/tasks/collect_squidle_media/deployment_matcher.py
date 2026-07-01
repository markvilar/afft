"""Phase 1: match ACFR deployments to Squidle+ deployments."""

from typing import Any

from afft.deployment import DeploymentInfo
from afft.squidle import Deployment, SquidleClient
from afft.utils.log import logger

from .types import (
    CollectSquidleMediaCommand,
    DeploymentKeyResolver,
    DeploymentLookupBuilder,
    DeploymentMatcher,
    DeploymentMatchPolicy,
    DeploymentState,
    TaskState,
)


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
    Create a ``(build_lookup, resolve_key)`` matcher for the given policy.

    ``build_lookup`` turns a list of Squidle+ deployments into a lookup keyed
    by the match key; ``resolve_key`` derives the match key from an ACFR
    deployment state.

    Arguments
    ---------
    policy: Strategy for matching ACFR deployments to Squidle+ deployments.

    Returns
    -------
    Tuple of ``(build_lookup, resolve_key)`` callables.
    """
    build_lookup: DeploymentLookupBuilder
    resolve_key: DeploymentKeyResolver

    if policy is DeploymentMatchPolicy.BY_NAME:

        def build_lookup(
            deployments: list[Deployment],
        ) -> dict[str, Deployment]:
            return {deployment.name: deployment for deployment in deployments}

        def resolve_key(entry: DeploymentState) -> str:
            return entry.deployment_info.metadata.acfr_deployment_label

    else:

        def build_lookup(
            deployments: list[Deployment],
        ) -> dict[str, Deployment]:
            return {
                _squidle_datetime_key(deployment.key): deployment
                for deployment in deployments
            }

        def resolve_key(entry: DeploymentState) -> str:
            return _acfr_datetime_key(entry.deployment_info.deployment_label)

    return build_lookup, resolve_key


def _fetch_platform_deployments(
    client: SquidleClient,
    platform_name: str,
) -> list[Deployment]:
    """
    Resolve a platform by name and fetch all of its deployments.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    platform_name: Platform name to resolve.

    Returns
    -------
    List of deployments for the platform (empty if the platform is unknown).
    """
    platform_filters: list[dict[str, Any]] = [
        {"name": "name", "op": "eq", "val": platform_name}
    ]
    platforms = client.fetch_platforms(platform_filters)
    if not platforms:
        logger.warning(
            f"no Squidle+ platform found with name: {platform_name!r}"
        )
        return []
    platform_id: int = platforms[0].id
    logger.info(f"resolved platform {platform_name!r} → id={platform_id}")
    deployment_filters: list[dict[str, Any]] = [
        {"name": "platform_id", "op": "eq", "val": platform_id}
    ]
    deployments: list[Deployment] = client.fetch_deployments(deployment_filters)
    logger.info(
        f"fetched {len(deployments)} deployment(s) for {platform_name!r}"
    )
    return deployments


def build_squidle_lookup(
    client: SquidleClient,
    entries: list[DeploymentState],
    build_lookup: DeploymentLookupBuilder,
) -> dict[str, Deployment]:
    """
    Fetch Squidle+ deployments for the ACFR platforms and build the lookup.

    Resolves the distinct platform names across the entries (one API call per
    platform), fetches their deployments, and accumulates a single lookup.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    entries: Per-deployment states holding the ACFR platform names.
    build_lookup: Callable turning deployments into a keyed lookup.

    Returns
    -------
    Combined lookup from match key to Squidle+ deployment.
    """
    lookup: dict[str, Deployment] = {}
    platform_names: set[str] = {
        entry.deployment_info.deployment_platform
        for entry in entries
        if entry.deployment_info.deployment_platform
    }
    for platform_name in platform_names:
        deployments = _fetch_platform_deployments(client, platform_name)
        lookup.update(build_lookup(deployments))
    return lookup


def match_deployment(
    command: CollectSquidleMediaCommand,
    entry: DeploymentState,
    lookup: dict[str, Deployment],
    resolve_key: DeploymentKeyResolver,
) -> DeploymentState:
    """
    Match an ACFR deployment to a Squidle+ deployment.

    Derives the lookup key via ``resolve_key`` and sets ``squidle_deployment``
    if found. Logs a warning and leaves it unset otherwise.

    Arguments
    ---------
    command: Task command.
    entry: Per-deployment state.
    lookup: Mapping from match key to Squidle+ deployment.
    resolve_key: Callable extracting the match key from an entry.

    Returns
    -------
    The (mutated) entry.
    """
    acfr_label: str = entry.deployment_info.metadata.acfr_deployment_label
    lookup_key: str = resolve_key(entry)
    match: Deployment | None = lookup.get(lookup_key)
    if match is None:
        logger.warning(
            f"no Squidle+ deployment match for: {acfr_label!r} "
            f"(policy={command.match_policy.value}, key={lookup_key!r})"
        )
        return entry
    entry.squidle_deployment = match
    return entry


def match_deployments(
    command: CollectSquidleMediaCommand,
    client: SquidleClient,
    deployment_infos: list[DeploymentInfo],
) -> TaskState:
    """
    Build the task state and match each ACFR deployment (phase 1).

    Arguments
    ---------
    command: Task command.
    client: Authenticated Squidle+ client.
    deployment_infos: ACFR deployment entries loaded from TOML.

    Returns
    -------
    Task state with each entry's ``squidle_deployment`` set where matched.
    """
    state: TaskState = TaskState(
        deployments=[
            DeploymentState(deployment_info=info) for info in deployment_infos
        ]
    )
    build_lookup: DeploymentLookupBuilder
    resolve_key: DeploymentKeyResolver
    build_lookup, resolve_key = create_deployment_matcher(command.match_policy)
    lookup: dict[str, Deployment] = build_squidle_lookup(
        client, state.deployments, build_lookup
    )
    for entry in state.deployments:
        match_deployment(command, entry, lookup, resolve_key)
    return state
