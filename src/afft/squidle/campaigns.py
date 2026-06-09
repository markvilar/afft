"""Functions for the Squidle+ campaign resource."""

import json
from typing import Any

from .client import SquidleClient
from .types import Campaign


def fetch_campaign(client: SquidleClient, campaign_id: int) -> Campaign:
    """
    Fetch a single campaign by ID.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    campaign_id: Numeric campaign identifier.

    Returns
    -------
    Campaign object.
    """
    data: dict[str, Any] = client.get(f"/api/campaign/{campaign_id}")
    return _parse_campaign(data)


def fetch_campaigns(
    client: SquidleClient,
    filters: list[dict[str, Any]] | None = None,
) -> list[Campaign]:
    """
    Fetch campaigns, optionally filtered.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    filters: Optional list of restless-style filter dicts, e.g.
        ``[{"name": "name", "op": "ilike", "val": "%Tasmania%"}]``.

    Returns
    -------
    List of Campaign objects.
    """
    params: dict[str, Any] = {}
    if filters:
        params["q"] = json.dumps({"filters": filters})
    objects: list[dict[str, Any]] = client.get_pages(
        "/api/campaign", params=params
    )
    return [_parse_campaign(obj) for obj in objects]


def _parse_campaign(data: dict[str, Any]) -> Campaign:
    return Campaign(
        id=data["id"],
        key=data.get("key") or "",
        name=data.get("name") or "",
        deployment_count=data.get("deployment_count") or 0,
        media_count=data.get("media_count") or 0,
    )
