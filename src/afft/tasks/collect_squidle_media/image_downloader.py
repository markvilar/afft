"""Phase 3: download the image files for retrieved media (optional)."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from rich.console import Console
from rich.progress import Progress, TaskID

from afft.utils.log import logger

from .types import (
    CollectSquidleMediaCommand,
    DeploymentImagesDownload,
    DeploymentState,
    ImageDownload,
    ImageDownloadStatus,
    TaskState,
)


def plan_download(
    entry: DeploymentState,
    output_dir: Path,
) -> DeploymentImagesDownload:
    """
    Build the per-deployment download state (all images PENDING).

    Arguments
    ---------
    entry: Matched deployment state carrying the retrieved media.
    output_dir: Root output directory.

    Returns
    -------
    Download state with one PENDING image per media record.
    """
    label: str = entry.deployment_info.deployment_label
    image_dir: Path = output_dir / f"{label}_images"
    images: list[ImageDownload] = [
        ImageDownload(
            source=record.path_best,
            destination=image_dir / f"{record.key}.jpg",
        )
        for record in (entry.media or [])
    ]
    return DeploymentImagesDownload(deployment_label=label, images=images)


def download_image(
    fetch_bytes: Callable[[str], bytes],
    image: ImageDownload,
) -> None:
    """
    Download a single image, mutating its status in place.

    Skips images already on disk; writes to a ``.part`` temp file and renames
    atomically; records failures on the image rather than raising.

    Arguments
    ---------
    fetch_bytes: Callable returning the image bytes for a URL.
    image: The image download to execute.
    """
    try:
        if image.destination.exists():
            image.status = ImageDownloadStatus.SKIPPED
            return
        image.destination.parent.mkdir(parents=True, exist_ok=True)
        temp_file: Path = image.destination.with_suffix(
            image.destination.suffix + ".part"
        )
        temp_file.write_bytes(fetch_bytes(image.source))
        temp_file.rename(image.destination)
        image.status = ImageDownloadStatus.DOWNLOADED
    except Exception as error:  # isolate per-image failures
        image.status = ImageDownloadStatus.FAILED
        image.error = str(error)
        logger.warning(f"download failed {image.destination.name!r}: {error}")


def download_deployment(
    fetch_bytes: Callable[[str], bytes],
    download: DeploymentImagesDownload,
    max_workers: int,
    on_image: Callable[[], None] | None = None,
) -> None:
    """
    Download one deployment's images concurrently, mutating each in place.

    Arguments
    ---------
    fetch_bytes: Callable returning the image bytes for a URL.
    download: The deployment download state.
    max_workers: Number of concurrent image downloads.
    on_image: Optional callback invoked once per finished image.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: list[Future[None]] = [
            executor.submit(download_image, fetch_bytes, image)
            for image in download.images
        ]
        for future in as_completed(futures):
            future.result()  # image already mutated in place
            if on_image is not None:
                on_image()


def download_deployment_images(
    downloads: list[DeploymentImagesDownload],
    max_workers: int,
) -> None:
    """
    Download all deployments' images (deployments sequential, images parallel).

    Owns a dedicated, pooled HTTP client shared across the image threads. The
    outer progress bar tracks deployments; the inner bar tracks the current
    deployment's images.

    Arguments
    ---------
    downloads: Pre-built per-deployment download states (all PENDING).
    max_workers: Concurrent image downloads per deployment.
    """
    console: Console = Console()
    with httpx.Client(follow_redirects=True) as http:

        def fetch_bytes(url: str) -> bytes:
            response: httpx.Response = http.get(url)
            response.raise_for_status()
            return response.content

        with Progress(
            console=console, disable=not console.is_terminal
        ) as progress:
            overall: TaskID = progress.add_task(
                "Deployments", total=len(downloads)
            )
            for download in downloads:
                inner: TaskID = progress.add_task(
                    download.deployment_label, total=len(download.images)
                )

                def advance(task_id: TaskID = inner) -> None:
                    progress.advance(task_id)

                download_deployment(fetch_bytes, download, max_workers, advance)
                progress.remove_task(inner)
                progress.advance(overall)


def build_download_plan(
    command: CollectSquidleMediaCommand,
    state: TaskState,
) -> list[DeploymentImagesDownload]:
    """
    Build per-deployment image download states without downloading.

    Attaches each download state to ``entry.downloads`` so the run is
    inspectable and reportable via the task state, whether or not the images
    are subsequently downloaded.

    Arguments
    ---------
    command: Task command.
    state: Task state; matched entries with media get a download plan.

    Returns
    -------
    The per-deployment download states (all PENDING).
    """
    downloads: list[DeploymentImagesDownload] = []
    for entry in state.matched:
        if not entry.media:
            continue
        entry.downloads = plan_download(entry, command.output_dir)
        downloads.append(entry.downloads)
    return downloads
