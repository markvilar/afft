"""Actions for data processing task CLI commands."""

from datetime import datetime
from pathlib import Path

from afft.environment import load_environment
from afft.tasks.clip_tables import ClipTablesCommand, run_clip_tables
from afft.tasks.collect_squidle_media import (
    CollectSquidleMediaCommand,
    CollectSquidleMediaConfig,
    DeploymentMatchPolicy,
    run_collect_squidle_media,
)


def invoke_clip_tables(
    source_dir: str | Path,
    output_dir: str | Path,
    start: datetime,
    end: datetime,
    pattern: str = "*.csv",
    timestamp_column: str = "timestamp",
    timestamp_format: str = "ISO8601",
) -> None:
    """Clip rows in CSV files to the [start, end] time interval."""
    command = ClipTablesCommand(
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
        start=start,
        end=end,
        pattern=pattern,
        timestamp_column=timestamp_column,
        timestamp_format=timestamp_format,
    )
    run_clip_tables(command)


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
