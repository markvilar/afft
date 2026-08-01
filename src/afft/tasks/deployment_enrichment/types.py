"""Data types for the enrich descriptor task."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from afft.deployment import DeploymentDescriptor, EnrichmentSection


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


class EnrichDescriptorDiagnostics(BaseModel):
    """
    Accumulates issues encountered during the run for deferred reporting.

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


class EnrichDescriptorCommand(BaseModel):
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


class EnrichDescriptorResult(BaseModel):
    """
    Result of the enrich descriptor task.

    Attributes
    ----------
    descriptors: The enriched descriptors, in input order.
    diagnostics: Warnings from the run.
    """

    model_config = ConfigDict(frozen=True)

    descriptors: list[DeploymentDescriptor]
    diagnostics: EnrichDescriptorDiagnostics
