"""Enrichment of deployment descriptors from the live Squidle+ API."""

import threading

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any

from rich.console import Console
from rich.progress import Progress, TaskID

from afft.deployment import (
    DeploymentDescriptor,
    SquidleDescriptorSection,
    read_deployment_descriptors,
    write_deployment_descriptors,
)
from afft.squidle import Campaign, Deployment, Platform, SquidleClient
from afft.utils.log import logger

from .types import (
    DeploymentMatchPolicy,
    EnrichSquidleCommand,
    EnrichSquidleDiagnostics,
    EnrichSquidleResult,
)


class _SquidleLookupCache:
    """
    In-run, id-keyed, lock-guarded cache for campaign/platform lookups.

    Shared across worker threads for a single ``match_squidle_deployments``
    invocation; not persisted across runs.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._campaigns: dict[int, Campaign] = {}
        self._platforms: dict[int, Platform] = {}

    def campaign(self, client: SquidleClient, campaign_id: int) -> Campaign:
        """Fetch a campaign by id, caching the result."""
        with self._lock:
            cached: Campaign | None = self._campaigns.get(campaign_id)
        if cached is not None:
            return cached
        campaign: Campaign = client.fetch_campaign(campaign_id)
        with self._lock:
            self._campaigns[campaign_id] = campaign
        return campaign

    def platform(self, client: SquidleClient, platform_id: int) -> Platform:
        """Fetch a platform by id, caching the result."""
        with self._lock:
            cached: Platform | None = self._platforms.get(platform_id)
        if cached is not None:
            return cached
        platform: Platform = client.fetch_platform(platform_id)
        with self._lock:
            self._platforms[platform_id] = platform
        return platform


def _acfr_datetime_key(deployment_label: str) -> str:
    """
    Extract ``{YYYYMMDD}_{HHMMSS}`` from an ACFR deployment label.

    ACFR deployment labels follow the format ``{geohash}_{YYYYMMDD}_{HHMMSS}``.
    """
    parts: list[str] = deployment_label.rsplit("_", 2)
    return f"{parts[-2]}_{parts[-1]}"


def resolve_squidle_deployment(
    client: SquidleClient,
    descriptor: DeploymentDescriptor,
    policy: DeploymentMatchPolicy,
) -> Deployment | None:
    """
    Resolve the Squidle+ deployment matching an ACFR deployment descriptor.

    Zero or more than one result is treated identically to "no match": the
    caller is left to warn and leave the descriptor's ``squidle`` section at
    its defaults. No silent first-match guessing, no hard error/abort.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    descriptor: ACFR deployment descriptor to match.
    policy: Strategy for matching ACFR deployments to Squidle+ deployments.

    Returns
    -------
    The matched Squidle+ deployment, or ``None`` if zero or ambiguous.
    """
    if policy is DeploymentMatchPolicy.BY_NAME:
        filters: list[dict[str, Any]] = [
            {"name": "name", "op": "eq", "val": descriptor.deployment_label}
        ]
    else:
        datetime_key: str = _acfr_datetime_key(descriptor.deployment_label)
        filters = [{"name": "key", "op": "ilike", "val": f"%{datetime_key}%"}]

    matches: list[Deployment] = client.fetch_deployments(filters)

    if not matches:
        logger.warning(
            f"no Squidle+ deployment match for: "
            f"{descriptor.deployment_label!r} (policy={policy.value})"
        )
        return None

    if len(matches) > 1:
        candidate_ids: str = ", ".join(str(match.id) for match in matches)
        logger.warning(
            f"ambiguous Squidle+ deployment match for: "
            f"{descriptor.deployment_label!r} (policy={policy.value}), "
            f"candidates: [{candidate_ids}]"
        )
        return None

    return matches[0]


def resolve_squidle_identity(
    client: SquidleClient,
    deployment: Deployment,
    cache: _SquidleLookupCache,
) -> SquidleDescriptorSection:
    """
    Fill a Squidle+ descriptor section from a matched deployment.

    Fills ``deployment_id``/``deployment_key``/``deployment_name`` directly,
    then fetches (or reads from cache) the campaign and platform by id to
    fill ``campaign_key``/``platform_key`` — the ``Deployment`` object itself
    only carries ``campaign_id``/``campaign_name`` and
    ``platform_id``/``platform_name``, no keys.

    A campaign or platform follow-up failure keeps whichever deployment
    fields did resolve and leaves only the failed campaign/platform fields at
    ``None`` — a successful deployment match is not discarded because of an
    unrelated follow-up failure.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    deployment: Matched Squidle+ deployment.
    cache: Shared in-run campaign/platform lookup cache.

    Returns
    -------
    The resolved Squidle+ descriptor section.
    """
    section = SquidleDescriptorSection(
        deployment_id=deployment.id,
        deployment_key=deployment.key,
        deployment_name=deployment.name,
        campaign_id=deployment.campaign_id,
        campaign_name=deployment.campaign_name,
        platform_id=deployment.platform_id,
        platform_name=deployment.platform_name,
    )

    try:
        campaign: Campaign = cache.campaign(client, deployment.campaign_id)
        section = section.model_copy(update={"campaign_key": campaign.key})
    except Exception as error:  # isolate campaign lookup failures
        logger.warning(
            f"failed to resolve Squidle+ campaign "
            f"{deployment.campaign_id} for deployment {deployment.id}: "
            f"{error}"
        )

    try:
        platform: Platform = cache.platform(client, deployment.platform_id)
        section = section.model_copy(update={"platform_key": platform.key})
    except Exception as error:  # isolate platform lookup failures
        logger.warning(
            f"failed to resolve Squidle+ platform "
            f"{deployment.platform_id} for deployment {deployment.id}: "
            f"{error}"
        )

    return section


def _match_descriptor(
    client: SquidleClient,
    descriptor: DeploymentDescriptor,
    policy: DeploymentMatchPolicy,
    cache: _SquidleLookupCache,
) -> DeploymentDescriptor:
    """Resolve and apply a descriptor's Squidle+ section."""
    match: Deployment | None = resolve_squidle_deployment(
        client, descriptor, policy
    )
    if match is None:
        return descriptor.model_copy(
            update={"squidle": SquidleDescriptorSection()}
        )
    section: SquidleDescriptorSection = resolve_squidle_identity(
        client, match, cache
    )
    return descriptor.model_copy(update={"squidle": section})


def match_squidle_deployments(
    descriptors: list[DeploymentDescriptor],
    client: SquidleClient,
    policy: DeploymentMatchPolicy = DeploymentMatchPolicy.BY_NAME,
    max_workers: int = 4,
) -> list[DeploymentDescriptor]:
    """
    Match a set of deployment descriptors against the live Squidle+ API.

    Runs the per-descriptor match + identity resolution concurrently via a
    thread pool, sharing one campaign/platform lookup cache across workers.

    Arguments
    ---------
    descriptors: Deployment descriptors to match.
    client: Authenticated Squidle+ client.
    policy: Strategy for matching ACFR deployments to Squidle+ deployments.
    max_workers: Maximum number of concurrent matching threads.

    Returns
    -------
    The descriptors with their ``squidle`` section resolved (or left at
    defaults where unmatched), in input order.
    """
    cache = _SquidleLookupCache()
    console: Console = Console()
    results: dict[int, DeploymentDescriptor] = {}

    with Progress(
        console=console,
        transient=True,
        disable=not console.is_terminal,
    ) as progress:
        task: TaskID = progress.add_task(
            "Matching Squidle+ deployments", total=len(descriptors)
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: dict[Future[DeploymentDescriptor], int] = {
                executor.submit(
                    _match_descriptor, client, descriptor, policy, cache
                ): index
                for index, descriptor in enumerate(descriptors)
            }
            try:
                for future in as_completed(futures):
                    index: int = futures[future]
                    results[index] = future.result()
                    progress.advance(task)
            except KeyboardInterrupt:
                # Cancel not-yet-started work so Ctrl+C does not block on the
                # whole queue; only in-flight matches still drain.
                console.print("Squidle+ matching interrupted; cancelling")
                executor.shutdown(wait=False, cancel_futures=True)
                raise

    return [results[index] for index in range(len(descriptors))]


def enrich_descriptors_from_squidle(
    command: EnrichSquidleCommand,
    client: SquidleClient,
) -> EnrichSquidleResult:
    """
    Match a descriptors file against the live Squidle+ API and write it back
    to TOML.

    Arguments
    ---------
    command: Task command.
    client: Authenticated Squidle+ client.

    Returns
    -------
    The written descriptors and the run's diagnostics.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    logger.info("-------------------------------------")
    logger.info("Enrich Deployment Descriptors (Squidle+)")
    logger.info(f"  input file:   {command.input_file}")
    logger.info(f"  output file:  {command.output_file}")
    logger.info(f"  match policy: {command.match_policy.value}")
    logger.info(f"  max workers:  {command.max_workers}")
    logger.info(f"  verbose:      {command.verbose}")
    logger.info("-------------------------------------")

    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        command.input_file
    )
    if not descriptors:
        raise ValueError(f"no deployments in {command.input_file}")

    logger.info(f"matching {len(descriptors)} deployment(s)")

    enriched: list[DeploymentDescriptor] = match_squidle_deployments(
        descriptors, client, command.match_policy, command.max_workers
    )

    diagnostics = EnrichSquidleDiagnostics()
    for descriptor in enriched:
        if descriptor.squidle.deployment_id is None:
            diagnostics.warning(
                descriptor.deployment_label, "no Squidle+ deployment matched"
            )
        elif descriptor.squidle.campaign_key is None:
            diagnostics.warning(
                descriptor.deployment_label,
                "Squidle+ deployment matched but campaign key unresolved",
            )
        elif descriptor.squidle.platform_key is None:
            diagnostics.warning(
                descriptor.deployment_label,
                "Squidle+ deployment matched but platform key unresolved",
            )

    write_deployment_descriptors(command.output_file, enriched)
    logger.info(
        f"wrote {len(enriched)} enriched deployment(s) to {command.output_file}"
    )

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.deployment_label}: {warning.message}")

    return EnrichSquidleResult(descriptors=enriched, diagnostics=diagnostics)
