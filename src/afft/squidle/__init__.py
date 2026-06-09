"""Package for interacting with the Squidle+ REST API."""

from .campaigns import fetch_campaign as fetch_campaign
from .campaigns import fetch_campaigns as fetch_campaigns
from .client import SquidleClient as SquidleClient
from .client import create_client as create_client
from .deployments import fetch_deployment as fetch_deployment
from .deployments import fetch_deployments as fetch_deployments
from .platforms import fetch_platform as fetch_platform
from .platforms import fetch_platforms as fetch_platforms
from .types import Campaign as Campaign
from .types import Deployment as Deployment
from .types import Platform as Platform

__all__ = []
