"""Data types for the deployment enrichment tasks."""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from afft.deployment import DeploymentDescriptor, EnrichmentSection


class DeploymentMatchPolicy(Enum):
    """
    Strategy for matching ACFR deployments to Squidle+ deployments.

    Attributes
    ----------
    BY_NAME: Match ``deployment_label`` against the Squidle+ name.
    BY_KEY: Match the ``{YYYYMMDD}_{HHMMSS}`` datetime embedded in the ACFR
        deployment label against the same prefix of the Squidle+ key.
    """

    BY_NAME = "by_name"
    BY_KEY = "by_key"


class EnrichmentWarning(BaseModel):
    """
    A non-fatal issue encountered while enriching one deployment.

    Attributes
    ----------
    deployment_label: Label of the deployment the issue belongs to.
    message: Human-readable description of the issue.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    message: str


class EnrichCatalogDiagnostics(BaseModel):
    """
    Accumulates issues encountered during a catalog enrichment run for
    deferred reporting.

    Attributes
    ----------
    warnings: Non-fatal issues, per deployment.
    """

    warnings: list[EnrichmentWarning] = Field(default_factory=list)

    def warning(self, deployment_label: str, message: str) -> None:
        """Append a warning for a deployment."""
        self.warnings.append(
            EnrichmentWarning(
                deployment_label=deployment_label, message=message
            )
        )


class EnrichCatalogCommand(BaseModel):
    """
    Command for enriching deployment descriptors from a curated catalog.

    Attributes
    ----------
    input_file: Path to the deployment descriptors TOML file.
    catalog_file: Path to the curated deployment catalog TOML file.
    output_file: Path to write the enriched descriptors as TOML; the input
        path enriches in place.
    section: The descriptor sections to fill.
    verbose: Log diagnostics warnings after the run completes.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    catalog_file: Path
    output_file: Path
    section: EnrichmentSection = EnrichmentSection.ALL
    verbose: bool = False


class EnrichCatalogResult(BaseModel):
    """
    Result of the enrich catalog task.

    Attributes
    ----------
    descriptors: The enriched descriptors, in input order.
    diagnostics: Warnings from the run.
    """

    model_config = ConfigDict(frozen=True)

    descriptors: list[DeploymentDescriptor]
    diagnostics: EnrichCatalogDiagnostics


class EnrichSquidleDiagnostics(BaseModel):
    """
    Accumulates issues encountered during a Squidle+ enrichment run for
    deferred reporting.

    Attributes
    ----------
    warnings: Non-fatal issues, per deployment.
    """

    warnings: list[EnrichmentWarning] = Field(default_factory=list)

    def warning(self, deployment_label: str, message: str) -> None:
        """Append a warning for a deployment."""
        self.warnings.append(
            EnrichmentWarning(
                deployment_label=deployment_label, message=message
            )
        )


class EnrichSquidleCommand(BaseModel):
    """
    Command for enriching deployment descriptors from the live Squidle+ API.

    Attributes
    ----------
    input_file: Path to the deployment descriptors TOML file.
    output_file: Path to write the enriched descriptors as TOML; the input
        path enriches in place.
    match_policy: Strategy for matching ACFR deployments to Squidle+
        deployments.
    max_workers: Concurrency bound for the per-deployment matching calls.
    verbose: Log diagnostics warnings after the run completes.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    output_file: Path
    match_policy: DeploymentMatchPolicy = DeploymentMatchPolicy.BY_NAME
    max_workers: int = 4
    verbose: bool = False


class EnrichSquidleResult(BaseModel):
    """
    Result of the enrich Squidle+ task.

    Attributes
    ----------
    descriptors: The enriched descriptors, in input order.
    diagnostics: Warnings from the run.
    """

    model_config = ConfigDict(frozen=True)

    descriptors: list[DeploymentDescriptor]
    diagnostics: EnrichSquidleDiagnostics
