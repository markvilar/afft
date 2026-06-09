"""Actions for Squidle+ CLI commands."""

from typing import Any

import pandas as pd

from afft.utils.log import logger
from afft.squidle import (
    Campaign,
    Deployment,
    Platform,
    create_client,
    fetch_campaigns,
    fetch_deployments,
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
