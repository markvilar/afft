"""Actions for deployment CLI commands."""

from pathlib import Path

from afft.tasks.deployment_descriptor import (
    DescribeDeploymentCommand,
    DescribeDeploymentResult,
    run_describe_deployment,
)


def dispatch_describe_deployment(
    root_dir: str | Path,
    output_file: str | Path,
    deployment_suffix: str = "_deployment_data",
    verbose: bool = False,
) -> None:
    """
    Describe the deployments under an ACFR deployment data directory tree.

    Exits non-zero if any deployment was skipped, so a partial run is visible
    to the caller without discarding the deployments that succeeded.
    """
    command = DescribeDeploymentCommand(
        root_dir=Path(root_dir),
        output_file=Path(output_file),
        deployment_suffix=deployment_suffix,
        verbose=verbose,
    )
    result: DescribeDeploymentResult = run_describe_deployment(command)
    if result.diagnostics.failures:
        raise SystemExit(1)
