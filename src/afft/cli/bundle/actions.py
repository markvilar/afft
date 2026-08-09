"""Actions for deployment bundle CLI commands."""

from pathlib import Path

from afft.tasks.build_deployment_bundle import (
    BuildDeploymentBundleCommand,
    read_build_deployment_bundle_config,
    run_build_deployment_bundle,
)
from afft.tasks.process_deployment_bundle import (
    ProcessDeploymentBundleCommand,
    run_process_deployment_bundle,
)


def dispatch_build_deployment_bundle(
    descriptor_file: str | Path,
    deployment_label: str,
    data_dir: str | Path,
    config_file: str | Path,
    output_file: str | Path,
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Build a deployment bundle from a descriptor and its raw message logs."""
    command = BuildDeploymentBundleCommand(
        descriptor_file=Path(descriptor_file),
        deployment_label=deployment_label,
        data_dir=Path(data_dir),
        config_file=Path(config_file),
        output_file=Path(output_file),
        overwrite=overwrite,
        verbose=verbose,
    )
    config = read_build_deployment_bundle_config(command.config_file)
    run_build_deployment_bundle(command, config)


def dispatch_process_deployment_bundle(
    input_file: str | Path,
    config_file: str | Path,
    output_file: str | Path,
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Run the configured processing pipeline over a deployment bundle."""
    command = ProcessDeploymentBundleCommand(
        input_file=input_file,
        config_file=config_file,
        output_file=output_file,
        overwrite=overwrite,
        verbose=verbose,
    )
    run_process_deployment_bundle(command)
