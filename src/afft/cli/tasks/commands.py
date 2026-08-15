"""
CLI commands for invoking data processing tasks.
"""

import click

from afft.tasks.collect_squidle_media import DeploymentMatchPolicy

from .actions import invoke_collect_squidle_media


@click.group()
@click.pass_context
def task_group(context: click.Context) -> None:
    """CLI group for invoking data processing tasks."""
    context.ensure_object(dict)


@task_group.command()
@click.option(
    "--deployments-file",
    "deployments_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="path to the ACFR deployments TOML file",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="directory to write one CSV per deployment",
)
@click.option(
    "--match-policy",
    "match_policy",
    type=click.Choice(
        [p.value for p in DeploymentMatchPolicy], case_sensitive=False
    ),
    default=DeploymentMatchPolicy.BY_NAME.value,
    show_default=True,
    help="strategy for matching ACFR deployments to Squidle+ deployments",
)
@click.option(
    "--max-workers",
    "max_workers",
    type=int,
    default=4,
    show_default=True,
    help="maximum number of concurrent deployment fetch threads",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="stop after deployment matching without fetching media",
)
@click.option(
    "--download-images",
    "download_images",
    is_flag=True,
    default=False,
    help="download image files after retrieving media records",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log skipped deployments after the run completes",
)
def collect_squidle_media(
    deployments_file: str,
    output_dir: str,
    match_policy: str,
    max_workers: int,
    dry_run: bool,
    download_images: bool,
    verbose: bool,
) -> None:
    """Fetch Squidle+ media for all deployments in the ACFR deployments file."""
    invoke_collect_squidle_media(
        deployments_file,
        output_dir,
        DeploymentMatchPolicy(match_policy),
        max_workers,
        dry_run,
        download_images,
        verbose,
    )
