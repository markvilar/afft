"""Data types for Squidle+ API resources."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Campaign:
    """
    Squidle+ campaign.

    Attributes
    ----------
    id: Numeric campaign identifier.
    key: Unique string identifier.
    name: Display name.
    deployment_count: Number of deployments in this campaign.
    media_count: Number of media items across all deployments.
    """

    id: int
    key: str
    name: str
    deployment_count: int
    media_count: int


@dataclass(slots=True, frozen=True)
class Platform:
    """
    Squidle+ platform.

    Attributes
    ----------
    id: Numeric platform identifier.
    key: Unique string identifier.
    name: Display name.
    """

    id: int
    key: str
    name: str


@dataclass(slots=True, frozen=True)
class Deployment:
    """
    Squidle+ deployment.

    Attributes
    ----------
    id: Numeric deployment identifier.
    key: Unique string identifier.
    name: Display name.
    campaign_id: ID of the parent campaign.
    campaign_name: Name of the parent campaign.
    platform_id: ID of the associated platform.
    platform_name: Name of the associated platform.
    timestamp_start: Start timestamp (ISO 8601), or None if not set.
    timestamp_end: End timestamp (ISO 8601), or None if not set.
    media_count: Number of media items in this deployment.
    pose_count: Number of pose estimates in this deployment.
    is_valid: Whether the deployment is marked as valid.
    """

    id: int
    key: str
    name: str
    campaign_id: int
    campaign_name: str
    platform_id: int
    platform_name: str
    timestamp_start: str | None
    timestamp_end: str | None
    media_count: int
    pose_count: int
    is_valid: bool
