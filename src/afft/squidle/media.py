"""Functions for fetching Squidle+ media and pose data."""

from typing import Any

from .transport import Operation, SquidleTransport
from .deployments import fetch_deployment, fetch_deployments
from .types import Deployment, DeploymentMedia, MediaRecord


def submit_deployment_export(
    transport: SquidleTransport,
    deployment_id: int,
) -> Operation:
    """
    Submit the media export operation for a deployment.

    Triggers the server-side export and returns a handle immediately, without
    blocking. Call ``result()`` on the handle to await and retrieve the raw
    media objects.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    deployment_id: Numeric deployment identifier.

    Returns
    -------
    Operation handle for the deployment's media export.
    """
    return transport.submit_operation(f"/api/deployment/{deployment_id}/export")


def fetch_media(
    transport: SquidleTransport,
    deployment_id: int,
) -> list[MediaRecord]:
    """
    Fetch all media and pose data for a single deployment.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    deployment_id: Numeric deployment identifier.

    Returns
    -------
    List of media records, one per media item.
    """
    operation: Operation = submit_deployment_export(transport, deployment_id)
    objects: list[dict[str, Any]] = operation.result()
    records: list[MediaRecord] = [_parse_media_record(obj) for obj in objects]
    return records


def fetch_deployment_media(
    transport: SquidleTransport,
    deployment_id: int,
) -> DeploymentMedia:
    """
    Fetch a deployment together with its media records.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    deployment_id: Numeric deployment identifier.

    Returns
    -------
    The deployment and its associated media records.
    """
    deployment: Deployment = fetch_deployment(transport, deployment_id)
    media: list[MediaRecord] = fetch_media(transport, deployment_id)
    return DeploymentMedia(deployment=deployment, media=media)


def fetch_media_batch(
    transport: SquidleTransport,
    deployment_ids: list[int],
) -> dict[int, list[MediaRecord]]:
    """
    Fetch media and pose data for multiple deployments.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    deployment_ids: List of numeric deployment identifiers.

    Returns
    -------
    Mapping from deployment ID to list of media records.
    """
    results: dict[int, list[MediaRecord]] = {}
    for deployment_id in deployment_ids:
        results[deployment_id] = fetch_media(transport, deployment_id)
    return results


def fetch_campaign_media(
    transport: SquidleTransport,
    campaign_id: int,
) -> dict[int, list[MediaRecord]]:
    """
    Fetch media and pose data for all deployments in a campaign.

    Arguments
    ---------
    transport: Authenticated Squidle+ transport.
    campaign_id: Numeric campaign identifier.

    Returns
    -------
    Mapping from deployment ID to list of media records.
    """
    filters: list[dict[str, Any]] = [
        {"name": "campaign_id", "op": "eq", "val": campaign_id}
    ]
    deployments = fetch_deployments(transport, filters)
    deployment_ids: list[int] = [deployment.id for deployment in deployments]
    return fetch_media_batch(transport, deployment_ids)


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
        pose_timestamp=pose.get("timestamp") or "",
        deployment_id=deployment.get("id") or 0,
        deployment_key=deployment.get("key") or "",
    )
