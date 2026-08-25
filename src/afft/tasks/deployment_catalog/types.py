"""Data types for the scaffold catalog task."""

from dataclasses import dataclass, field
from pathlib import Path

from afft.deployment import DeploymentCatalog


@dataclass(slots=True, frozen=True)
class CatalogWarning:
    """
    A non-fatal issue encountered while scaffolding the catalog.

    Attributes
    ----------
    deployment_label: Label of the deployment the issue belongs to.
    message: Human-readable description of the issue.
    """

    deployment_label: str
    message: str


@dataclass(slots=True)
class ScaffoldCatalogDiagnostics:
    """
    Accumulates issues encountered during the run for deferred reporting.

    Attributes
    ----------
    warnings: Non-fatal issues, per deployment.
    """

    warnings: list[CatalogWarning] = field(default_factory=list)

    def warning(self, deployment_label: str, message: str) -> None:
        """Append a warning for a deployment."""
        self.warnings.append(CatalogWarning(deployment_label, message))


@dataclass(slots=True, frozen=True)
class ScaffoldCatalogCommand:
    """
    Command for scaffolding a curated deployment catalog from a set of
    deployment descriptors.

    Attributes
    ----------
    input_file: Path to the deployment descriptors TOML file.
    output_file: Path to write the catalog skeleton as TOML.
    verbose: Log diagnostics warnings after the run completes.
    """

    input_file: Path
    output_file: Path
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class ScaffoldCatalogResult:
    """
    Result of the scaffold catalog task.

    Attributes
    ----------
    catalog: The scaffolded catalog skeleton.
    diagnostics: Warnings from the run.
    """

    catalog: DeploymentCatalog
    diagnostics: ScaffoldCatalogDiagnostics
