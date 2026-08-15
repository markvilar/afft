"""Actions for data processing task CLI commands."""

from pathlib import Path

from afft.environment import load_environment
from afft.tasks.collect_squidle_media import (
    CollectSquidleMediaCommand,
    CollectSquidleMediaConfig,
    DeploymentMatchPolicy,
    run_collect_squidle_media,
)


def invoke_collect_squidle_media(
    deployments_file: str | Path,
    output_dir: str | Path,
    match_policy: DeploymentMatchPolicy = DeploymentMatchPolicy.BY_NAME,
    max_workers: int = 4,
    dry_run: bool = False,
    download_images: bool = False,
    verbose: bool = False,
) -> None:
    """Invoke the collect Squidle+ media task."""
    token = load_environment().tokens.squidle
    if token is None:
        raise ValueError(
            "missing Squidle API token: set SQUIDLE_API_TOKEN in .env"
        )
    command = CollectSquidleMediaCommand(
        deployments_file=Path(deployments_file),
        output_dir=Path(output_dir),
        match_policy=match_policy,
        max_workers=max_workers,
        dry_run=dry_run,
        download_images=download_images,
        verbose=verbose,
    )
    config = CollectSquidleMediaConfig(squidle_token=token)
    run_collect_squidle_media(command, config)
