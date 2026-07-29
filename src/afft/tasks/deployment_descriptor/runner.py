"""Runner for the describe deployment task."""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from rich.progress import Progress

from afft.deployment import (
    DeploymentDescriptor,
    DeploymentFiles,
    collect_deployment_files,
    write_deployment_descriptors,
)
from afft.seabed import (
    SeabedSystemConfig,
    parse_localizer_config,
    parse_system_config,
)
from afft.utils.log import logger

from .builders import (
    build_deployment_file_section,
    build_deployment_metadata,
    build_sensor_section,
    build_system_section,
    build_telemetry_section,
)
from .types import (
    DescribeDeploymentCommand,
    DescribeDeploymentDiagnostics,
    DescribeDeploymentResult,
)

type DeploymentDatetimeFinder = Callable[[Path], datetime]
type DeploymentFinder = Callable[[Path], list[Path]]
type DeploymentLabeller = Callable[[Path], str]


def create_deployment_finder(
    command: DescribeDeploymentCommand,
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
    command: DescribeDeploymentCommand,
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
    command: DescribeDeploymentCommand,
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


def describe_deployment(
    directory: Path,
    deployment_label: str,
    deployment_datetime: datetime,
    diagnostics: DescribeDeploymentDiagnostics,
) -> DeploymentDescriptor:
    """
    Describe a single deployment directory.

    Resolves the deployment's files once, parses both SEABED configs, and maps
    the results onto the descriptor's sections. The localizer config is parsed
    for validation only — nothing from it reaches the descriptor.

    Arguments
    ---------
    directory: Deployment root directory.
    deployment_label: Label of the deployment.
    deployment_datetime: Start datetime of the deployment.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    The assembled deployment descriptor.

    Raises
    ------
    ValueError: If a required file is missing or duplicated, or if either
        SEABED config fails to parse.
    """
    files: DeploymentFiles = collect_deployment_files(directory)
    if files.other:
        diagnostics.warning(
            deployment_label,
            f"{len(files.other)} uncategorized file(s): "
            f"{', '.join(str(p.relative_to(files.root)) for p in files.other)}",
        )

    system_config: SeabedSystemConfig = parse_system_config(files.system_config)
    parse_localizer_config(files.localizer_config)

    sensors = build_sensor_section(system_config)
    if not sensors.sensors:
        diagnostics.warning(
            deployment_label, "empty sensor roster in the system config"
        )

    return DeploymentDescriptor(
        deployment_label=deployment_label,
        deployment_datetime=deployment_datetime,
        deployment_platform="",
        metadata=build_deployment_metadata(
            files, deployment_label, diagnostics
        ),
        files=build_deployment_file_section(files),
        telemetry=build_telemetry_section(files, deployment_label, diagnostics),
        sensors=sensors,
        system=build_system_section(system_config),
    )


def run_describe_deployment(
    command: DescribeDeploymentCommand,
) -> DescribeDeploymentResult:
    """
    Describe the deployments under an ACFR deployment data directory tree and
    write the descriptors to a TOML file.

    A deployment that cannot be described is skipped and recorded on the
    diagnostics; the remaining deployments are still written.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The written descriptors and the run's diagnostics.
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
    logger.info("Describe Deployments")
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
        f"describing {len(deployment_dirs)} deployment(s) under "
        f"{command.root_dir}"
    )

    diagnostics = DescribeDeploymentDiagnostics()
    descriptors: list[DeploymentDescriptor] = []
    progress = Progress()
    task = progress.add_task(
        "Describing deployments", total=len(deployment_dirs)
    )
    progress.start()
    for deployment_dir in deployment_dirs:
        # The label keys every diagnostic, so derive it before anything that
        # can fail.
        label: str = label_deployment(deployment_dir)
        progress.update(task, description=f"Describing deployments - {label}")
        try:
            descriptors.append(
                describe_deployment(
                    deployment_dir,
                    label,
                    find_start_datetime(deployment_dir),
                    diagnostics,
                )
            )
        except (OSError, ValueError) as error:
            diagnostics.failure(label, str(error))
        progress.advance(task)
    progress.stop()

    write_deployment_descriptors(command.output_file, descriptors)
    logger.info(
        f"wrote {len(descriptors)} deployment(s) to {command.output_file}"
    )

    for failure in diagnostics.failures:
        logger.error(f"skipped {failure.deployment_label}: {failure.reason}")

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.deployment_label}: {warning.message}")

    return DescribeDeploymentResult(
        descriptors=descriptors, diagnostics=diagnostics
    )
