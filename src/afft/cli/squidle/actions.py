"""Actions for Squidle+ CLI commands."""

from pathlib import Path
from typing import Any

import pandas as pd

from afft.utils.log import logger

from afft.squidle import (
    Campaign,
    Deployment,
    Platform,
    create_client,
    fetch_campaign_media,
    fetch_campaigns,
    fetch_deployments,
    fetch_media,
    fetch_media_batch,
    fetch_platforms,
)


def dispatch_list_platforms(name: str | None = None) -> None:
    """Fetch and print platforms, optionally filtered by name."""
    filters: list[dict[str, Any]] = []
    if name:
        filters.append({"name": "name", "op": "ilike", "val": f"%{name}%"})

    with create_client() as client:
        platforms: list[Platform] = fetch_platforms(client, filters or None)

    if not platforms:
        logger.info("No platforms found.")
        return

    dataframe: pd.DataFrame = pd.DataFrame(
        [
            {
                "id": platform.id,
                "key": platform.key,
                "name": platform.name,
            }
            for platform in platforms
        ]
    )
    logger.info("\n" + dataframe.to_string(index=False))


def dispatch_collect_deployment(
    deployment_id: int,
    output_file: Path,
) -> None:
    """Fetch media for a single deployment and write to CSV."""
    with create_client() as client:
        dataframe: pd.DataFrame = fetch_media(client, deployment_id)
    dataframe.to_csv(output_file, index=False)
    logger.info(
        f"deployment {deployment_id}: {len(dataframe)} record(s) → {output_file}"
    )


def dispatch_collect_deployments(
    deployment_ids: list[int],
    output_dir: Path,
) -> None:
    """Fetch media for multiple deployments and write one CSV per deployment."""
    with create_client() as client:
        results: dict[int, pd.DataFrame] = fetch_media_batch(
            client, deployment_ids
        )
    for deployment_id, dataframe in results.items():
        output_file: Path = output_dir / f"{deployment_id}_squidle_media.csv"
        dataframe.to_csv(output_file, index=False)
        logger.info(
            f"deployment {deployment_id}: {len(dataframe)} record(s) "
            f"→ {output_file.name}"
        )


def dispatch_collect_campaign(
    campaign_id: int,
    output_dir: Path,
) -> None:
    """Fetch media for all deployments in a campaign, one CSV per deployment."""
    with create_client() as client:
        results: dict[int, pd.DataFrame] = fetch_campaign_media(
            client, campaign_id
        )
    for deployment_id, dataframe in results.items():
        if dataframe.empty:
            continue
        deployment_key: str = (
            dataframe["deployment_key"].iloc[0]
            if "deployment_key" in dataframe.columns
            else str(deployment_id)
        )
        output_file: Path = output_dir / f"{deployment_key}_squidle_media.csv"
        dataframe.to_csv(output_file, index=False)
        logger.info(
            f"deployment {deployment_id}: {len(dataframe)} record(s) "
            f"→ {output_file.name}"
        )


def dispatch_list_campaigns(name: str | None = None) -> None:
    """Fetch and print campaigns, optionally filtered by name."""
    filters: list[dict[str, Any]] = []
    if name:
        filters.append({"name": "name", "op": "ilike", "val": f"%{name}%"})

    with create_client() as client:
        campaigns: list[Campaign] = fetch_campaigns(client, filters or None)

    if not campaigns:
        logger.info("No campaigns found.")
        return

    dataframe: pd.DataFrame = pd.DataFrame(
        [
            {
                "id": campaign.id,
                "key": campaign.key,
                "name": campaign.name,
                "deployments": campaign.deployment_count,
                "media": campaign.media_count,
            }
            for campaign in campaigns
        ]
    )
    logger.info("\n" + dataframe.to_string(index=False))


def dispatch_list_deployments(
    campaign_id: int | None = None,
    name: str | None = None,
) -> None:
    """Fetch and print deployments, optionally filtered by campaign or name."""
    filters: list[dict[str, Any]] = []
    if campaign_id is not None:
        filters.append({"name": "campaign_id", "op": "eq", "val": campaign_id})
    if name:
        filters.append({"name": "name", "op": "ilike", "val": f"%{name}%"})

    with create_client() as client:
        deployments: list[Deployment] = fetch_deployments(
            client, filters or None
        )

    if not deployments:
        logger.info("No deployments found.")
        return

    dataframe: pd.DataFrame = pd.DataFrame(
        [
            {
                "id": deployment.id,
                "key": deployment.key,
                "name": deployment.name,
                "campaign": deployment.campaign_name,
                "platform": deployment.platform_name,
                "media": deployment.media_count,
                "poses": deployment.pose_count,
                "valid": deployment.is_valid,
            }
            for deployment in deployments
        ]
    )
    logger.info("\n" + dataframe.to_string(index=False))
