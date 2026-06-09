"""Functions for the Squidle+ platform resource."""

import json
from typing import Any

from .client import SquidleClient
from .types import Platform


def fetch_platform(client: SquidleClient, platform_id: int) -> Platform:
    """
    Fetch a single platform by ID.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    platform_id: Numeric platform identifier.

    Returns
    -------
    Platform object.
    """
    data: dict[str, Any] = client.get(f"/api/platform/{platform_id}")
    return _parse_platform(data)


def fetch_platforms(
    client: SquidleClient,
    filters: list[dict[str, Any]] | None = None,
) -> list[Platform]:
    """
    Fetch platforms, optionally filtered.

    Arguments
    ---------
    client: Authenticated Squidle+ client.
    filters: Optional list of restless-style filter dicts, e.g.
        ``[{"name": "name", "op": "ilike", "val": "%sirius%"}]``.

    Returns
    -------
    List of Platform objects.
    """
    params: dict[str, Any] = {}
    if filters:
        params["q"] = json.dumps({"filters": filters})
    objects: list[dict[str, Any]] = client.get_pages(
        "/api/platform", params=params
    )
    return [_parse_platform(obj) for obj in objects]


def _parse_platform(data: dict[str, Any]) -> Platform:
    return Platform(
        id=data["id"],
        key=data.get("key") or "",
        name=data.get("name") or "",
    )
