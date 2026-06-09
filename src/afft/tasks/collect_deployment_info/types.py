"""Data types for the collect deployment info task."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

type DeploymentDatetimeFinder = Callable[[Path], datetime]
type DeploymentFinder = Callable[[Path], list[Path]]
type DeploymentLabeller = Callable[[Path], str]


@dataclass(slots=True, frozen=True)
class DeploymentMetadata:
    """
    Collected metadata for a single AUV deployment.

    Attributes
    ----------
    acfr_deployment_label: ACFR mission file stem.
    acfr_campaign_label: ACFR campaign directory name.
    origin_latitude: Deployment origin latitude in decimal degrees.
    origin_longitude: Deployment origin longitude in decimal degrees.
    magnetic_variation: Magnetic variation at the origin in degrees.
    message_topics: Sorted unique message topic names from the RAW AUV logs.
    renav_labels: Sorted renav run labels from the camera poses directory.
    camera_calibration_files: Sorted unique camera calibration filenames.
    """

    acfr_deployment_label: str
    acfr_campaign_label: str
    origin_latitude: float
    origin_longitude: float
    magnetic_variation: float
    message_topics: list[str]
    renav_labels: list[str]
    camera_calibration_files: list[str]


@dataclass(slots=True, frozen=True)
class DeploymentInfo:
    """
    Core identity fields for a single AUV deployment.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_datetime: Deployment datetime.
    metadata: Collected deployment metadata.
    """

    deployment_label: str
    deployment_datetime: datetime
    metadata: DeploymentMetadata


@dataclass(slots=True, frozen=True)
class CollectDeploymentInfoResult:
    """
    Result of the collect deployment info task.

    Attributes
    ----------
    deployments: Collected metadata for each deployment.
    """

    deployments: list[DeploymentInfo]


@dataclass(slots=True)
class CollectDeploymentInfoDiagnostics:
    """
    Accumulates non-fatal issues encountered during the collect deployment
    info task for deferred reporting after the run completes.

    Attributes
    ----------
    warnings: Collected warning messages.
    """

    warnings: list[str] = field(default_factory=list)

    def warning(self, message: str) -> None:
        """Append a warning message."""
        self.warnings.append(message)


@dataclass(slots=True, frozen=True)
class CollectDeploymentInfoCommand:
    """
    Command for collecting deployment metadata from an ACFR deployment data
    directory tree and writing the result to a TOML file.

    Attributes
    ----------
    root_dir: Root directory containing deployment subdirectories.
    output_file: Path to write the collected deployment info as TOML.
    deployment_suffix: Suffix stripped from each deployment subdirectory name
        to derive the deployment label (e.g. ``"_deployment_data"``).
    verbose: Log diagnostics warnings after the run completes.
    """

    root_dir: Path
    output_file: Path
    deployment_suffix: str = "_deployment_data"
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class CollectDeploymentInfoConfig:
    """
    Configuration for the collect deployment info task.

    Attributes
    ----------
    """
