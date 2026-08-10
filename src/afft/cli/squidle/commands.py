"""CLI commands for the Squidle+ API."""

import click

from pathlib import Path

from .actions import (
    invoke_collect_campaign,
    invoke_collect_deployment,
    invoke_collect_deployments,
    invoke_list_campaigns,
    invoke_list_deployments,
    invoke_list_platforms,
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
    invoke_list_platforms(name)


@squidle_group.command()
@click.option(
    "--name",
    type=str,
    default=None,
    help="filter campaigns by name (case-insensitive substring match)",
)
def list_campaigns(name: str | None) -> None:
    """List Squidle+ campaigns."""
    invoke_list_campaigns(name)


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
    invoke_list_deployments(campaign_id, name)


@squidle_group.command()
@click.option(
    "--deployment-id",
    "deployment_id",
    type=int,
    required=True,
    help="deployment ID to collect media for",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(dir_okay=False),
    required=True,
    help="path to write the media CSV",
)
def collect_deployment(deployment_id: int, output_file: str) -> None:
    """Fetch media for a single Squidle+ deployment and write to CSV."""
    invoke_collect_deployment(deployment_id, Path(output_file))


@squidle_group.command()
@click.option(
    "--deployment-ids",
    "deployment_ids",
    type=str,
    required=True,
    help="comma-separated list of deployment IDs",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write one CSV per deployment",
)
def collect_deployments(deployment_ids: str, output_dir: str) -> None:
    """Fetch media for multiple Squidle+ deployments and write one CSV each."""
    ids: list[int] = [int(i.strip()) for i in deployment_ids.split(",")]
    invoke_collect_deployments(ids, Path(output_dir))


@squidle_group.command()
@click.option(
    "--campaign-id",
    "campaign_id",
    type=int,
    required=True,
    help="campaign ID to collect media for",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write one CSV per deployment",
)
def collect_campaign(campaign_id: int, output_dir: str) -> None:
    """Fetch media for all deployments in a Squidle+ campaign."""
    invoke_collect_campaign(campaign_id, Path(output_dir))
