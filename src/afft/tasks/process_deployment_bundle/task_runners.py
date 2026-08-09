"""Runner for the process deployment bundle task."""

import os

from pathlib import Path

from afft.bundle_processing import (
    Pipeline,
    PipelineConfig,
    build_pipeline,
    run_pipeline,
    validate_pipeline,
)
from afft.deployment import (
    DeploymentBundleIO,
    DeploymentBundleReader,
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.utils.log import logger

from .task_helpers import (
    read_process_deployment_bundle_config,
    validate_process_deployment_bundle_input,
)
from .task_types import (
    ProcessDeploymentBundleCommand,
    ProcessDeploymentBundleResult,
)


def run_process_deployment_bundle(
    command: ProcessDeploymentBundleCommand,
) -> ProcessDeploymentBundleResult:
    """
    Run the configured processing pipeline over one deployment bundle.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The run's result, naming the keys the pipeline's steps wrote.

    Raises
    ------
    FileNotFoundError: If the input bundle or the output directory does not
        exist.
    ValueError: If the output file is the input file, if it already exists
        and ``overwrite`` is not set, or if the pipeline is not runnable
        against the input bundle.
    PipelineStepError: If a step fails. Propagates from ``run_pipeline``
        uncaught; the staged output is removed first.
    """
    validate_process_deployment_bundle_input(command)

    config: PipelineConfig = read_process_deployment_bundle_config(
        command.config_file
    )
    pipeline: Pipeline = build_pipeline(config)

    logger.info("-------------------------------------")
    logger.info("Process Deployment Bundle")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  steps:       {len(pipeline)}")
    logger.info("-------------------------------------")

    output_file: Path = command.output_file
    staged: Path = output_file.with_suffix(".partial" + output_file.suffix)
    try:
        reader: DeploymentBundleReader
        target: DeploymentBundleIO
        with open_deployment_bundle_reader(command.input_file) as reader:
            validate_pipeline(pipeline, set(reader.list_frames()))
            with open_deployment_bundle(staged) as target:
                run_pipeline(pipeline, reader, target, verbose=command.verbose)
        os.replace(staged, output_file)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise

    logger.info(f"wrote processed deployment bundle to {output_file}")

    return ProcessDeploymentBundleResult(
        input_file=command.input_file,
        output_file=output_file,
        output_keys=tuple(step.output for step in pipeline),
    )
