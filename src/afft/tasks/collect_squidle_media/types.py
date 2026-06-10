"""Data types for the collect Squidle+ media task."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from afft.squidle.types import Deployment
from afft.tasks.collect_deployment_info import DeploymentInfo


type DeploymentKeyResolver = Callable[["DeploymentMediaContext"], str]
type DeploymentLookupBuilder = Callable[
    [list[Deployment]], dict[str, Deployment]
]
type DeploymentMatcher = tuple[DeploymentLookupBuilder, DeploymentKeyResolver]


class DeploymentMatchPolicy(Enum):
    """
    Strategy for matching ACFR deployments to Squidle+ deployments.

    Attributes
    ----------
    NAME: Match ``acfr_deployment_label`` against the Squidle+ deployment name.
    KEY: Match the datetime embedded in ``deployment_label`` against the
        ``{YYYYMMDD}_{HHMMSS}`` prefix of the Squidle+ deployment key.
    """

    BY_NAME = "by_name"
    BY_KEY = "by_key"


@dataclass(slots=True, frozen=True)
class CollectSquidleMediaCommand:
    """
    Command for collecting Squidle+ media for ACFR deployments.

    Attributes
    ----------
    deployments_file: Path to the ACFR deployments TOML file.
    output_dir: Directory to write one CSV per deployment.
    match_policy: Strategy for matching ACFR to Squidle+ deployments.
    verbose: Log skipped deployments after the run completes.
    """

    deployments_file: Path
    output_dir: Path
    match_policy: DeploymentMatchPolicy = DeploymentMatchPolicy.BY_NAME
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class CollectSquidleMediaConfig:
    """
    Configuration for the collect Squidle+ media task.

    Attributes
    ----------
    """


@dataclass(slots=True)
class DeploymentMediaContext:
    """
    Per-deployment state accumulated across the processing chain.

    Attributes
    ----------
    acfr_deployment: ACFR deployment entry loaded from TOML. Always present.
    squidle_deployment: Matched Squidle+ deployment. Set by the match step.
    media: Raw media records from Squidle+. Set by the fetch step.
    result: Annotated media DataFrame. Set by the format step.
    """

    acfr_deployment: DeploymentInfo
    squidle_deployment: Deployment | None = None
    media: pd.DataFrame | None = None
    result: pd.DataFrame | None = None


@dataclass(slots=True)
class CollectSquidleMediaContext:
    """
    High-level context holding per-deployment state for the full task run.

    Attributes
    ----------
    deployments: One context object per ACFR deployment entry.
    """

    deployments: list[DeploymentMediaContext]


@dataclass(slots=True, frozen=True)
class CollectSquidleMediaResult:
    """
    Result of the collect Squidle+ media task.

    Attributes
    ----------
    exported: Paths of CSV files written.
    skipped: ACFR deployment labels for which no Squidle+ match was found.
    """

    exported: list[Path]
    skipped: list[str]
