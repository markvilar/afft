"""Runner for the collect deployment info task."""

import dataclasses

from datetime import datetime, timezone
from pathlib import Path

import msgspec

from tqdm.auto import tqdm

from afft.utils.log import logger

from .collectors import (
    collect_acfr_campaign_label,
    collect_acfr_deployment_label,
    collect_camera_calibration_files,
    collect_magnetic_variation,
    collect_message_topics,
    collect_origin_latitude,
    collect_origin_longitude,
    collect_renav_labels,
)
from .types import (
    CollectDeploymentInfoCommand,
    CollectDeploymentInfoConfig,
    CollectDeploymentInfoDiagnostics,
    CollectDeploymentInfoResult,
    DeploymentDatetimeFinder,
    DeploymentFinder,
    DeploymentInfo,
    DeploymentLabeller,
    DeploymentMetadata,
)


def create_deployment_finder(
    command: CollectDeploymentInfoCommand,
) -> DeploymentFinder:
    """
    Create a strategy that finds deployment subdirectories under a root directory.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    Callable that takes a root directory and returns a sorted list of
    deployment subdirectories matching the suffix.
    """
    suffix: str = command.deployment_suffix

    def finder(root_dir: Path) -> list[Path]:
        return sorted(
            child
            for child in root_dir.iterdir()
            if child.is_dir() and child.name.endswith(suffix)
        )

    return finder


def create_deployment_labeller(
    command: CollectDeploymentInfoCommand,
) -> DeploymentLabeller:
    """
    Create a strategy that derives a deployment label from a directory path.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    Callable that takes a deployment directory and returns its label string.
    """

    suffix: str = command.deployment_suffix

    def labeller(directory: Path) -> str:
        return directory.name.removesuffix(suffix)

    return labeller


def create_deployment_datetime_finder(
    command: CollectDeploymentInfoCommand,
) -> DeploymentDatetimeFinder:
    """
    Create a strategy that parses the start datetime from a deployment
    directory name.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    Callable that takes a deployment directory and returns its start datetime.
    Raises ``ValueError`` if the datetime cannot be parsed from the name.
    """
    suffix: str = command.deployment_suffix

    def finder(directory: Path) -> datetime:
        label: str = directory.name.removesuffix(suffix)
        parts: list[str] = label.rsplit("_", 2)
        if len(parts) < 3:
            raise ValueError(
                f"cannot parse datetime from directory name: {directory.name}"
            )
        return datetime.strptime(
            f"{parts[-2]}_{parts[-1]}", "%Y%m%d_%H%M%S"
        ).replace(tzinfo=timezone.utc)

    return finder


def run_collect_deployment_info(
    command: CollectDeploymentInfoCommand,
    config: CollectDeploymentInfoConfig,
) -> CollectDeploymentInfoResult:
    """
    Collect deployment metadata from an ACFR deployment data directory tree
    and write the results to a TOML file.

    Arguments
    ---------
    command: Task command.
    config: Task configuration.
    """
    if not command.root_dir.exists():
        raise FileNotFoundError(
            f"root directory does not exist: {command.root_dir}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    logger.info("-------------------------------------")
    logger.info("Collect Deployment Info")
    logger.info(f"  root dir:          {command.root_dir}")
    logger.info(f"  output file:       {command.output_file}")
    logger.info(f"  deployment suffix: {command.deployment_suffix}")
    logger.info(f"  verbose:           {command.verbose}")
    logger.info("-------------------------------------")

    find_deployments: DeploymentFinder = create_deployment_finder(command)
    label_deployment: DeploymentLabeller = create_deployment_labeller(command)
    find_start_datetime: DeploymentDatetimeFinder = (
        create_deployment_datetime_finder(command)
    )

    deployment_dirs: list[Path] = find_deployments(command.root_dir)
    if not deployment_dirs:
        raise FileNotFoundError(
            f"no deployment directories ending in "
            f"{command.deployment_suffix!r} found under {command.root_dir}"
        )

    logger.info(
        f"collecting deployment info from {len(deployment_dirs)} "
        f"deployment(s) under {command.root_dir}"
    )

    diagnostics: CollectDeploymentInfoDiagnostics = (
        CollectDeploymentInfoDiagnostics()
    )
    deployments: list[DeploymentInfo] = []
    progress: tqdm = tqdm(deployment_dirs, desc="Collecting deployment info")
    for deployment_dir in progress:
        label: str = label_deployment(deployment_dir)
        deployment_datetime: datetime = find_start_datetime(deployment_dir)
        progress.set_description(f"Collecting deployment info - {label}")
        deployments.append(
            DeploymentInfo(
                deployment_label=label,
                deployment_datetime=deployment_datetime,
                deployment_platform="",
                metadata=DeploymentMetadata(
                    acfr_deployment_label=collect_acfr_deployment_label(
                        deployment_dir, config, diagnostics
                    ),
                    acfr_campaign_label=collect_acfr_campaign_label(
                        deployment_dir, config, diagnostics
                    ),
                    acfr_platform_label="",
                    origin_latitude=collect_origin_latitude(
                        deployment_dir, config, diagnostics
                    ),
                    origin_longitude=collect_origin_longitude(
                        deployment_dir, config, diagnostics
                    ),
                    magnetic_variation=collect_magnetic_variation(
                        deployment_dir, config, diagnostics
                    ),
                    message_topics=collect_message_topics(
                        deployment_dir, config, diagnostics
                    ),
                    renav_labels=collect_renav_labels(
                        deployment_dir, config, diagnostics
                    ),
                    camera_calibration_files=collect_camera_calibration_files(
                        deployment_dir, config, diagnostics
                    ),
                ),
            )
        )

    result: CollectDeploymentInfoResult = CollectDeploymentInfoResult(
        deployments=deployments
    )
    command.output_file.write_bytes(
        msgspec.toml.encode(
            {"deployments": [dataclasses.asdict(d) for d in result.deployments]}
        )
    )
    logger.info(
        f"wrote {len(result.deployments)} deployment(s) to {command.output_file}"
    )

    if command.verbose:
        for message in diagnostics.warnings:
            logger.warning(message)

    return result
