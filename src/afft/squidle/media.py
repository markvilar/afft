"""Functions for fetching Squidle+ media and pose data."""

from typing import Any

import pandas as pd

from afft.utils.log import logger

from .client import SquidleClient
from .deployments import fetch_deployments
from .types import MediaRecord


_MEDIA_COLUMNS: list[str] = [
    "key",
    "path_best",
    "timestamp",
    "pose_lat",
    "pose_lon",
    "pose_alt",
    "pose_dep",
    "deployment_id",
    "deployment_key",
]


def fetch_media(
    client: SquidleClient,
    deployment_id: int,
) -> pd.DataFrame:
    """
    Fetch all media and pose data for a single deployment.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    deployment_id: Numeric deployment identifier.

    Returns
    -------
    DataFrame with one row per media item and columns matching
    ``MediaRecord`` fields.
    """
    objects: list[dict[str, Any]] = client.export_deployment(deployment_id)
    records: list[MediaRecord] = [_parse_media_record(obj) for obj in objects]
    logger.info(
        f"deployment {deployment_id}: fetched {len(records)} media record(s)"
    )
    return _to_dataframe(records)


def fetch_media_batch(
    client: SquidleClient,
    deployment_ids: list[int],
) -> dict[int, pd.DataFrame]:
    """
    Fetch media and pose data for multiple deployments.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    deployment_ids: List of numeric deployment identifiers.

    Returns
    -------
    Mapping from deployment ID to DataFrame of media records.
    """
    results: dict[int, pd.DataFrame] = {}
    for deployment_id in deployment_ids:
        results[deployment_id] = fetch_media(client, deployment_id)
    return results


def fetch_campaign_media(
    client: SquidleClient,
    campaign_id: int,
) -> dict[int, pd.DataFrame]:
    """
    Fetch media and pose data for all deployments in a campaign.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    campaign_id: Numeric campaign identifier.

    Returns
    -------
    Mapping from deployment ID to DataFrame of media records.
    """
    filters: list[dict[str, Any]] = [
        {"name": "campaign_id", "op": "eq", "val": campaign_id}
    ]
    deployments = fetch_deployments(client, filters)
    logger.info(
        f"campaign {campaign_id}: found {len(deployments)} deployment(s)"
    )
    deployment_ids: list[int] = [deployment.id for deployment in deployments]
    return fetch_media_batch(client, deployment_ids)


def _parse_media_record(data: dict[str, Any]) -> MediaRecord:
    pose: dict[str, Any] = data.get("pose") or {}
    deployment: dict[str, Any] = data.get("deployment") or {}
    return MediaRecord(
        key=data.get("key") or "",
        path_best=data.get("path_best") or "",
        timestamp=data.get("timestamp_start") or "",
        pose_lat=pose.get("lat") or 0.0,
        pose_lon=pose.get("lon") or 0.0,
        pose_alt=pose.get("alt") or 0.0,
        pose_dep=pose.get("dep") or 0.0,
        deployment_id=deployment.get("id") or 0,
        deployment_key=deployment.get("key") or "",
    )


def _to_dataframe(records: list[MediaRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "key": record.key,
                "path_best": record.path_best,
                "timestamp": record.timestamp,
                "pose_lat": record.pose_lat,
                "pose_lon": record.pose_lon,
                "pose_alt": record.pose_alt,
                "pose_dep": record.pose_dep,
                "deployment_id": record.deployment_id,
                "deployment_key": record.deployment_key,
            }
            for record in records
        ],
        columns=_MEDIA_COLUMNS,
    )
