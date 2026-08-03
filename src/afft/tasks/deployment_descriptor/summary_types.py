"""Data types for the summarize descriptors task."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from afft.deployment import DescriptorSummary


class SummarizeDescriptorCommand(BaseModel):
    """
    Command for summarizing the deployments in a descriptor file.

    Attributes
    ----------
    input_file: Path to the deployment descriptors TOML file.
    output_file: Path to write the detailed report as Markdown; ``None``
        prints the brief summary to the terminal instead.
    verbose: List the offending deployment labels in the terminal summary.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    output_file: Path | None = None
    verbose: bool = False


class SummarizeDescriptorResult(BaseModel):
    """
    Result of the summarize descriptors task.

    Attributes
    ----------
    summary: The computed summary.
    output_file: Path the report was written to; ``None`` if the summary was
        only logged.
    """

    model_config = ConfigDict(frozen=True)

    summary: DescriptorSummary
    output_file: Path | None
