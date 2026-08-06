"""Data types for the build deployment bundle task."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from afft.deployment import DeploymentDescriptor, DeploymentFiles
from afft.seabed import Message, MessageTypeName, Topic


@dataclass(slots=True, frozen=True)
class BuildDeploymentBundleConfig:
    """
    Attributes
    ----------
    message_map: Mapping from message topic to message type name.
    """

    message_map: dict[Topic, MessageTypeName]


@dataclass(slots=True, frozen=True)
class BuildDeploymentBundleCommand:
    """
    Attributes
    ----------
    descriptor_file: Path to the deployment descriptors TOML file containing
        the target deployment's (enriched) descriptor.
    deployment_label: Label of the deployment to build, selected out of
        ``descriptor_file``'s entries.
    data_dir: Per-deployment data directory, e.g.
        ``<root_dir>/qdch0ftq_20100428_020202_deployment_data``.
    config_file: Path to the shared task config TOML file
        (``config/default.toml``).
    output_file: Path to write the deployment bundle to.
    verbose: Log diagnostics warnings after the run completes.
    """

    descriptor_file: Path
    deployment_label: str
    data_dir: Path
    config_file: Path
    output_file: Path
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class BuildDeploymentBundleWarning:
    """
    Attributes
    ----------
    topic: Message topic the warning concerns.
    message: Human-readable description of the issue.
    """

    topic: str
    message: str


@dataclass(slots=True)
class BuildDeploymentBundleDiagnostics:
    """
    Accumulates issues encountered during the build for deferred reporting.

    Attributes
    ----------
    warnings: Non-fatal issues, per topic.
    """

    warnings: list[BuildDeploymentBundleWarning] = field(default_factory=list)

    def warning(self, topic: str, message: str) -> None:
        """Append a warning for a topic."""
        self.warnings.append(BuildDeploymentBundleWarning(topic, message))


@dataclass(slots=True, frozen=True)
class BuildDeploymentBundleResult:
    """
    Attributes
    ----------
    deployment_label: Label of the deployment the bundle was built for.
    output_file: Path the bundle was written to.
    diagnostics: Warnings from the run.
    """

    deployment_label: str
    output_file: Path
    diagnostics: BuildDeploymentBundleDiagnostics


@dataclass(slots=True, frozen=True)
class BuildDeploymentBundleData:
    """
    Attributes
    ----------
    descriptor: Enriched descriptor for the deployment being built.
    files: Deployment's file manifest, from `collect_deployment_files`.
    message_groups: Parsed raw messages, grouped by topic and sorted by
        timestamp.
    """

    descriptor: DeploymentDescriptor
    files: DeploymentFiles
    message_groups: dict[Topic, list[Message[Any, Any]]]
