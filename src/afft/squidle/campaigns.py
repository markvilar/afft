"""Functions for the Squidle+ campaign resource."""

import json
from typing import Any

from .transport import SquidleTransport
from .types import Campaign


def fetch_campaign(transport: SquidleTransport, campaign_id: int) -> Campaign:
    """
    Fetch a single campaign by ID.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    campaign_id: Numeric campaign identifier.

    Returns
    -------
    Campaign object.
    """
    data: dict[str, Any] = transport.get(f"/api/campaign/{campaign_id}")
    return _parse_campaign(data)


def fetch_campaigns(
    transport: SquidleTransport,
    filters: list[dict[str, Any]] | None = None,
) -> list[Campaign]:
    """
    Fetch campaigns, optionally filtered.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    filters: Optional list of restless-style filter dicts, e.g.
        ``[{"name": "name", "op": "ilike", "val": "%Tasmania%"}]``.

    Returns
    -------
    List of Campaign objects.
    """
    params: dict[str, Any] = {}
    if filters:
        params["q"] = json.dumps({"filters": filters})
    objects: list[dict[str, Any]] = transport.get_pages(
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
