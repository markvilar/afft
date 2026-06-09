"""CLI commands for the Squidle+ API."""

import click

from .actions import (
    dispatch_list_campaigns,
    dispatch_list_deployments,
    dispatch_list_platforms,
)


@click.group()
@click.pass_context
def squidle_group(context: click.Context) -> None:
    """CLI group for Squidle+ API commands."""
    context.ensure_object(dict)


@squidle_group.command()
@click.option(
    "--name",
    type=str,
    default=None,
    help="filter platforms by name (case-insensitive substring match)",
)
def list_platforms(name: str | None) -> None:
    """List Squidle+ platforms."""
    dispatch_list_platforms(name)


@squidle_group.command()
@click.option(
    "--name",
    type=str,
    default=None,
    help="filter campaigns by name (case-insensitive substring match)",
)
def list_campaigns(name: str | None) -> None:
    """List Squidle+ campaigns."""
    dispatch_list_campaigns(name)


@squidle_group.command()
@click.option(
    "--campaign-id",
    "campaign_id",
    type=int,
    default=None,
    help="filter deployments by campaign ID",
)
@click.option(
    "--name",
    type=str,
    default=None,
    help="filter deployments by name (case-insensitive substring match)",
)
def list_deployments(campaign_id: int | None, name: str | None) -> None:
    """List Squidle+ deployments."""
    dispatch_list_deployments(campaign_id, name)
