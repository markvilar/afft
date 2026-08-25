"""Fluent facade over the Squidle+ API."""

from types import TracebackType
from typing import Any

from .campaigns import fetch_campaign as _fetch_campaign
from .campaigns import fetch_campaigns as _fetch_campaigns
from .deployments import fetch_deployment as _fetch_deployment
from .deployments import fetch_deployments as _fetch_deployments
from .media import fetch_campaign_media as _fetch_campaign_media
from .media import fetch_deployment_media as _fetch_deployment_media
from .media import fetch_media as _fetch_media
from .media import fetch_media_batch as _fetch_media_batch
from .media import submit_deployment_export as _submit_deployment_export
from .platforms import fetch_platform as _fetch_platform
from .platforms import fetch_platforms as _fetch_platforms
from .transport import Operation, SquidleTransport, SquidleTransportConfig
from .types import Campaign, Deployment, DeploymentMedia, MediaRecord, Platform


class SquidleClient:
    """
    Fluent facade over the Squidle+ API.

    Wraps a SquidleTransport and exposes one method per endpoint, delegating to
    the resource functions. Use as a context manager to close the underlying
    connection:

        with create_client(token) as client:
            campaigns = client.fetch_campaigns()
    """

    def __init__(
        self,
        token: str,
        config: SquidleTransportConfig | None = None,
    ) -> None:
        self._transport: SquidleTransport = SquidleTransport(token, config)

    def __enter__(self) -> "SquidleClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._transport.close()

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._transport.close()

    def fetch_platform(self, platform_id: int) -> Platform:
        """Fetch a single platform by ID."""
        return _fetch_platform(self._transport, platform_id)

    def fetch_platforms(
        self, filters: list[dict[str, Any]] | None = None
    ) -> list[Platform]:
        """Fetch platforms, optionally filtered."""
        return _fetch_platforms(self._transport, filters)

    def fetch_campaign(self, campaign_id: int) -> Campaign:
        """Fetch a single campaign by ID."""
        return _fetch_campaign(self._transport, campaign_id)

    def fetch_campaigns(
        self, filters: list[dict[str, Any]] | None = None
    ) -> list[Campaign]:
        """Fetch campaigns, optionally filtered."""
        return _fetch_campaigns(self._transport, filters)

    def fetch_deployment(self, deployment_id: int) -> Deployment:
        """Fetch a single deployment by ID."""
        return _fetch_deployment(self._transport, deployment_id)

    def fetch_deployments(
        self, filters: list[dict[str, Any]] | None = None
    ) -> list[Deployment]:
        """Fetch deployments, optionally filtered."""
        return _fetch_deployments(self._transport, filters)

    def submit_deployment_export(self, deployment_id: int) -> Operation:
        """Submit the media export operation for a deployment."""
        return _submit_deployment_export(self._transport, deployment_id)

    def fetch_media(self, deployment_id: int) -> list[MediaRecord]:
        """Fetch all media and pose data for a single deployment."""
        return _fetch_media(self._transport, deployment_id)

    def fetch_deployment_media(self, deployment_id: int) -> DeploymentMedia:
        """Fetch a deployment together with its media records."""
        return _fetch_deployment_media(self._transport, deployment_id)

    def fetch_media_batch(
        self, deployment_ids: list[int]
    ) -> dict[int, list[MediaRecord]]:
        """Fetch media and pose data for multiple deployments."""
        return _fetch_media_batch(self._transport, deployment_ids)

    def fetch_campaign_media(
        self, campaign_id: int
    ) -> dict[int, list[MediaRecord]]:
        """Fetch media and pose data for all deployments in a campaign."""
        return _fetch_campaign_media(self._transport, campaign_id)


def create_client(
    token: str,
    config: SquidleTransportConfig | None = None,
) -> SquidleClient:
    """
    Create a SquidleClient facade from an API token.

    Arguments
    ---------
    token: Squidle+ API token used to authenticate requests.
    config: Optional transport request-behaviour configuration. Defaults are
        used if not provided.

    Returns
    -------
    Authenticated SquidleClient facade.
    """
    return SquidleClient(token=token, config=config)
