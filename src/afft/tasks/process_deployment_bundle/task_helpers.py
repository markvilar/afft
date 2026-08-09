"""Supporting functions for the process deployment bundle task: config
loading and input validation."""

from pathlib import Path
from typing import Any

import afft.io as io

from afft.bundle_processing import PipelineConfig

from .task_types import ProcessDeploymentBundleCommand


def read_process_deployment_bundle_config(
    config_file: Path,
) -> PipelineConfig:
    """
    Read the processing pipeline section from the shared task config file.

    Arguments
    ---------
    config_file: Path to the shared task config TOML file.

    Returns
    -------
    The pipeline as declared in the config file.
    """
    raw: dict[str, Any] = io.read_config(config_file)
    section: dict[str, Any] = raw["afft"]["tasks"]["process_deployment_bundle"]

    return PipelineConfig(**section["pipeline"])


def validate_process_deployment_bundle_input(
    command: ProcessDeploymentBundleCommand,
) -> None:
    """
    Validate the task's inputs before any expensive work runs.

    Arguments
    ---------
    command: Task command.

    Raises
    ------
    FileNotFoundError: If the input bundle or the output directory does not
        exist.
    ValueError: If the output file resolves to the input file, or if it
        already exists and ``command.overwrite`` is not set.
    """
    if not command.input_file.is_file():
        raise FileNotFoundError(
            f"input bundle does not exist: {command.input_file}"
        )

    if not command.output_file.parent.is_dir():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    input_path: Path = command.input_file.resolve()
    output_path: Path = command.output_file.resolve()
    if output_path == input_path:
        raise ValueError(
            f"output file is the input file: {output_path} -- a run would "
            f"overwrite the bundle it reads from"
        )

    if command.output_file.exists() and not command.overwrite:
        raise ValueError(f"output file already exists: {command.output_file}")
