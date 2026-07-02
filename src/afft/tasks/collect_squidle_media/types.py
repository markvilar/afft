"""Data types for the collect Squidle+ media task."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from pydantic import SecretStr

from afft.deployment import DeploymentInfo
from afft.squidle import Deployment, MediaRecord


type DeploymentKeyResolver = Callable[["DeploymentState"], str]
type DeploymentLookupBuilder = Callable[
    [list[Deployment]], dict[str, Deployment]
]
type DeploymentMatcher = tuple[DeploymentLookupBuilder, DeploymentKeyResolver]


class DeploymentMatchPolicy(Enum):
    """
    Strategy for matching ACFR deployments to Squidle+ deployments.

    Attributes
    ----------
    BY_NAME: Match ``acfr_deployment_label`` against the Squidle+ name.
    BY_KEY: Match the ``{YYYYMMDD}_{HHMMSS}`` datetime embedded in the ACFR
        deployment label against the same prefix of the Squidle+ key.
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
    output_dir: Directory to write per-deployment CSVs and image subdirs.
    match_policy: Strategy for matching ACFR to Squidle+ deployments.
    max_workers: Concurrency bound (deployments in phase 2; images per
        deployment in phase 3).
    dry_run: Stop after deployment matching without fetching media.
    download_images: Download image files after retrieving media records.
    verbose: Log skipped deployments after the run completes.
    """

    deployments_file: Path
    output_dir: Path
    match_policy: DeploymentMatchPolicy = DeploymentMatchPolicy.BY_NAME
    max_workers: int = 4
    dry_run: bool = False
    download_images: bool = False
    verbose: bool = False


@dataclass(slots=True, frozen=True)
class CollectSquidleMediaConfig:
    """
    Configuration for the collect Squidle+ media task.

    Attributes
    ----------
    squidle_token: Squidle+ API token, resolved from the environment by the
        CLI and injected here. Kept as SecretStr to avoid accidental leakage.
    """

    squidle_token: SecretStr


class ImageDownloadStatus(Enum):
    """Status of a single image download."""

    PENDING = "pending"
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(slots=True)
class ImageDownload:
    """
    Per-image download state.

    Attributes
    ----------
    source: Image URL (``MediaRecord.path_best``).
    destination: Path the image is written to on disk.
    status: Current download status.
    error: Error message if the download failed.
    """

    source: str
    destination: Path
    status: ImageDownloadStatus = ImageDownloadStatus.PENDING
    error: str | None = None


@dataclass(slots=True)
class DeploymentImagesDownload:
    """
    All image downloads for a single deployment.

    Self-contained (carries the deployment label), built upfront with every
    image PENDING and mutated in place as the download runs.

    Attributes
    ----------
    deployment_label: ACFR deployment label; names the output subdirectory.
    images: Per-image download states.
    """

    deployment_label: str
    images: list[ImageDownload]

    def _by_status(self, status: ImageDownloadStatus) -> list[ImageDownload]:
        return [image for image in self.images if image.status is status]

    @property
    def pending(self) -> list[ImageDownload]:
        """Images not yet attempted."""
        return self._by_status(ImageDownloadStatus.PENDING)

    @property
    def downloaded(self) -> list[ImageDownload]:
        """Images written successfully."""
        return self._by_status(ImageDownloadStatus.DOWNLOADED)

    @property
    def skipped(self) -> list[ImageDownload]:
        """Images already present on disk."""
        return self._by_status(ImageDownloadStatus.SKIPPED)

    @property
    def failed(self) -> list[ImageDownload]:
        """Images whose download failed."""
        return self._by_status(ImageDownloadStatus.FAILED)


@dataclass(slots=True)
class DeploymentState:
    """
    Per-deployment state accumulated across the task phases.

    Attributes
    ----------
    deployment_info: ACFR deployment entry loaded from TOML. Always present.
    squidle_deployment: Matched Squidle+ deployment. Set by phase 1.
    media: Media records from Squidle+. Set by phase 2.
    result: Annotated media DataFrame. Set by phase 2.
    error: Retrieval error message if the export failed. Set by phase 2.
    downloads: Per-deployment image downloads. Set by phase 3.
    """

    deployment_info: DeploymentInfo
    squidle_deployment: Deployment | None = None
    media: list[MediaRecord] | None = None
    result: pd.DataFrame | None = None
    error: str | None = None
    downloads: DeploymentImagesDownload | None = None

    @property
    def matched(self) -> bool:
        """True if a Squidle+ deployment has been matched."""
        return self.squidle_deployment is not None

    @property
    def unmatched(self) -> bool:
        """True if no Squidle+ deployment has been matched."""
        return self.squidle_deployment is None

    @property
    def failed(self) -> bool:
        """True if matched but media retrieval errored."""
        return self.squidle_deployment is not None and self.error is not None


@dataclass(slots=True)
class TaskState:
    """
    Mutable per-run state holding one entry per ACFR deployment.

    Attributes
    ----------
    deployments: One state object per ACFR deployment entry.
    """

    deployments: list[DeploymentState]

    @property
    def matched(self) -> list[DeploymentState]:
        """Entries with a resolved Squidle+ match."""
        return [entry for entry in self.deployments if entry.matched]

    @property
    def unmatched(self) -> list[DeploymentState]:
        """Entries with no Squidle+ match."""
        return [entry for entry in self.deployments if entry.unmatched]


@dataclass(slots=True, frozen=True)
class MatchSummary:
    """Summary of phase 1 (loading and matching)."""

    loaded: int
    matched: int
    unmatched: list[str]


@dataclass(slots=True, frozen=True)
class RetrievalSummary:
    """Summary of phase 2 (media retrieval)."""

    attempted: int
    exported: list[Path]
    failed: list[str]


@dataclass(slots=True, frozen=True)
class DownloadSummary:
    """Summary of phase 3 (image downloading)."""

    deployments: int
    downloaded: int
    skipped: int
    failed: int


@dataclass(slots=True, frozen=True)
class DownloadReport:
    """
    Image download outcomes for one deployment.

    Attributes
    ----------
    images: The per-image download states.
    """

    images: list[ImageDownload]

    def _count(self, status: ImageDownloadStatus) -> int:
        return sum(1 for image in self.images if image.status is status)

    @property
    def downloaded(self) -> int:
        """Number of images written successfully."""
        return self._count(ImageDownloadStatus.DOWNLOADED)

    @property
    def skipped(self) -> int:
        """Number of images already present on disk."""
        return self._count(ImageDownloadStatus.SKIPPED)

    @property
    def failed(self) -> int:
        """Number of images whose download failed."""
        return self._count(ImageDownloadStatus.FAILED)

    @property
    def failures(self) -> list[ImageDownload]:
        """The failed image downloads."""
        return [
            image
            for image in self.images
            if image.status is ImageDownloadStatus.FAILED
        ]


@dataclass(slots=True, frozen=True)
class DeploymentReport:
    """
    Record of what one ACFR deployment produced during a run.

    Attributes
    ----------
    acfr_deployment_label: ACFR deployment label.
    acfr_campaign_label: ACFR campaign label.
    matched: Whether a Squidle+ deployment was matched.
    squidle_deployment_id: Matched Squidle+ deployment id, if any.
    squidle_deployment_key: Matched Squidle+ deployment key, if any.
    squidle_deployment_name: Matched Squidle+ deployment name, if any.
    squidle_campaign_name: Matched Squidle+ campaign name, if any.
    squidle_platform_name: Matched Squidle+ platform name, if any.
    media_records_file: Exported CSV path, if written.
    media_record_count: Number of media records retrieved.
    retrieval_error: Media retrieval error message, if any.
    download: Image download outcomes, if a download plan was built.
    """

    acfr_deployment_label: str
    acfr_campaign_label: str
    matched: bool
    squidle_deployment_id: int | None
    squidle_deployment_key: str | None
    squidle_deployment_name: str | None
    squidle_campaign_name: str | None
    squidle_platform_name: str | None
    media_records_file: str | None
    media_record_count: int
    retrieval_error: str | None
    download: DownloadReport | None


@dataclass(slots=True, frozen=True)
class RunReport:
    """
    Durable, JSON-serializable summary of one collector run.

    Attributes
    ----------
    deployments_file: Path to the ACFR deployments TOML used for the run.
    output_dir: Root output directory.
    deployments: One report per ACFR deployment.
    """

    deployments_file: str
    output_dir: str
    deployments: list[DeploymentReport]
