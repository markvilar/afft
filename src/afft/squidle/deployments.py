"""Functions for the Squidle+ deployment resource."""

import json
from typing import Any

from .client import SquidleClient
from .types import Deployment


def fetch_deployment(client: SquidleClient, deployment_id: int) -> Deployment:
    """
    Fetch a single deployment by ID.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    deployment_id: Numeric deployment identifier.

    Returns
    -------
    Deployment object.
    """
    data: dict[str, Any] = client.get(f"/api/deployment/{deployment_id}")
    return _parse_deployment(data)


def fetch_deployments(
    client: SquidleClient,
    filters: list[dict[str, Any]] | None = None,
) -> list[Deployment]:
    """
    Fetch deployments, optionally filtered.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    filters: Optional list of restless-style filter dicts, e.g.
        ``[{"name": "campaign_id", "op": "eq", "val": 42}]``.

    Returns
    -------
    List of Deployment objects.
    """
    params: dict[str, Any] = {}
    if filters:
        params["q"] = json.dumps({"filters": filters})
    objects: list[dict[str, Any]] = client.get_pages(
        "/api/deployment", params=params
    )
    return [_parse_deployment(obj) for obj in objects]


def _parse_deployment(data: dict[str, Any]) -> Deployment:
    campaign: dict[str, Any] = data.get("campaign") or {}
    platform: dict[str, Any] = data.get("platform") or {}
    return Deployment(
        id=data["id"],
        key=data.get("key") or "",
        name=data.get("name") or "",
        campaign_id=campaign.get("id") or 0,
        campaign_name=campaign.get("name") or "",
        platform_id=platform.get("id") or 0,
        platform_name=platform.get("name") or "",
        timestamp_start=data.get("timestamp_start"),
        timestamp_end=data.get("timestamp_end"),
        media_count=data.get("media_count") or 0,
        pose_count=data.get("pose_count") or 0,
        is_valid=data.get("is_valid") or False,
    )
