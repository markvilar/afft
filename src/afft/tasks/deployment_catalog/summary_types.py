"""Data types for the summarize catalog task."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from afft.deployment import CatalogSummary


class SummarizeCatalogCommand(BaseModel):
    """
    Command for summarizing a curated deployment catalog.

    Attributes
    ----------
    input_file: Path to the deployment catalog TOML file.
    verbose: List the offending profile and deployment keys in the terminal
        summary.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    verbose: bool = False


class SummarizeCatalogResult(BaseModel):
    """
    Result of the summarize catalog task.

    Attributes
    ----------
    summary: The computed summary.
    """

    model_config = ConfigDict(frozen=True)

    summary: CatalogSummary
