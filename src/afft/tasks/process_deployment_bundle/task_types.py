"""Data types for the process deployment bundle task."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ProcessDeploymentBundleCommand(BaseModel):
    """
    Attributes
    ----------
    input_file: Path to the source deployment bundle, read but never written.
    config_file: Path to the shared task config TOML file
        (``config/default.toml``).
    output_file: Path to write the processed deployment bundle to. Must
        differ from ``input_file``.
    overwrite: Overwrite ``output_file`` if it already exists.
    verbose: Log each step's output key as it is written.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    config_file: Path
    output_file: Path
    overwrite: bool = False
    verbose: bool = False


class ProcessDeploymentBundleResult(BaseModel):
    """
    Attributes
    ----------
    input_file: Path the run read from.
    output_file: Path the completed bundle was moved to.
    output_keys: Bundle keys the pipeline's steps wrote, in run order.
    """

    model_config = ConfigDict(frozen=True)

    input_file: Path
    output_file: Path
    output_keys: tuple[str, ...]
