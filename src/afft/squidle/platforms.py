"""Functions for the Squidle+ platform resource."""

import json
from typing import Any

from .transport import SquidleTransport
from .types import Platform


def fetch_platform(transport: SquidleTransport, platform_id: int) -> Platform:
    """
    Fetch a single platform by ID.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    platform_id: Numeric platform identifier.

    Returns
    -------
    Platform object.
    """
    data: dict[str, Any] = transport.get(f"/api/platform/{platform_id}")
    return _parse_platform(data)


def fetch_platforms(
    transport: SquidleTransport,
    filters: list[dict[str, Any]] | None = None,
) -> list[Platform]:
    """
    Fetch platforms, optionally filtered.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    filters: Optional list of restless-style filter dicts, e.g.
        ``[{"name": "name", "op": "ilike", "val": "%sirius%"}]``.

    Returns
    -------
    List of Platform objects.
    """
    params: dict[str, Any] = {}
    if filters:
        params["q"] = json.dumps({"filters": filters})
    objects: list[dict[str, Any]] = transport.get_pages(
        "/api/platform", params=params
    )
    return [_parse_platform(obj) for obj in objects]


def _parse_platform(data: dict[str, Any]) -> Platform:
    return Platform(
        id=data["id"],
        key=data.get("key") or "",
        name=data.get("name") or "",
    )
