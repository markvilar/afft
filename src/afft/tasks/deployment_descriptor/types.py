"""Data types for the describe deployment task."""

from dataclasses import dataclass, field
from pathlib import Path

from afft.deployment import DeploymentDescriptor


@dataclass(slots=True, frozen=True)
class DeploymentWarning:
    """
    A non-fatal issue encountered while describing one deployment.

    Attributes
    ----------
    deployment_label: Label of the deployment the issue belongs to.
    message: Human-readable description of the issue.
    """

    deployment_label: str
    message: str


@dataclass(slots=True, frozen=True)
class DeploymentFailure:
    """
    A deployment that could not be described and was skipped.

    Attributes
    ----------
    deployment_label: Label of the skipped deployment.
    reason: Human-readable cause, typically the string form of the error.
    """

    deployment_label: str
    reason: str


@dataclass(slots=True)
class DescribeDeploymentDiagnostics:
    """
    Accumulates issues encountered during the run for deferred reporting.

    Attributes
    ----------
    warnings: Non-fatal issues, per deployment.
    failures: Deployments that were skipped.
    """

    warnings: list[DeploymentWarning] = field(default_factory=list)
    failures: list[DeploymentFailure] = field(default_factory=list)

    def warning(self, deployment_label: str, message: str) -> None:
        """Append a warning for a deployment."""
        self.warnings.append(DeploymentWarning(deployment_label, message))

    def failure(self, deployment_label: str, reason: str) -> None:
        """Append a skipped deployment and its cause."""
        self.failures.append(DeploymentFailure(deployment_label, reason))


@dataclass(slots=True, frozen=True)
class DescribeDeploymentCommand:
    """
    Command for describing the deployments under an ACFR deployment data
    directory tree and writing the descriptors to a TOML file.

    Attributes
    ----------
    root_dir: Root directory containing deployment subdirectories.
    output_file: Path to write the deployment descriptors as TOML.
    deployment_suffix: Suffix stripped from each deployment subdirectory name
        to derive the deployment label (e.g. ``"_deployment_data"``).
    verbose: Log diagnostics warnings after the run completes.
    """

    root_dir: Path
    output_file: Path
    deployment_suffix: str = "_deployment_data"
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class DescribeDeploymentResult:
    """
    Result of the describe deployment task.

    Attributes
    ----------
    descriptors: Descriptors for the deployments that were described.
    diagnostics: Warnings and skipped deployments from the run.
    """

    descriptors: list[DeploymentDescriptor]
    diagnostics: DescribeDeploymentDiagnostics
