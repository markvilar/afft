"""Runner for the collect renav stereo poses task."""

import re
import shutil

from pathlib import Path

from afft.renav.readers import RENAV_SKIP_ROWS
from afft.utils.log import logger

from .types import CollectRenavStereoPosesCommand


_POSE_FILE_GLOB = "camera_poses/renav*_stereo_pose_est.data"
_DATE_PATTERN = re.compile(r"renav(\d{8})_stereo_pose_est")


def _count_data_rows(path: Path) -> int:
    total: int = sum(1 for line in path.open() if line.strip())
    return max(0, total - RENAV_SKIP_ROWS)


def _extract_date(path: Path) -> str:
    match = _DATE_PATTERN.search(path.name)
    return match.group(1) if match else ""


def _select_file(candidates: list[Path], tiebreak_margin: float) -> Path:
    if len(candidates) == 1:
        return candidates[0]

    counts: dict[Path, int] = {
        path: _count_data_rows(path) for path in candidates
    }
    max_count: int = max(counts.values())
    threshold: float = max_count * (1.0 - tiebreak_margin)

    top: list[Path] = [
        path for path, count in counts.items() if count >= threshold
    ]
    return max(top, key=_extract_date)


def run_collect_renav_stereo_poses(
    command: CollectRenavStereoPosesCommand,
) -> None:
    """
    Find, select, and copy Renav stereo pose estimate files to an output
    directory with deployment-labelled filenames.

    For each deployment subdirectory under ``root_dir``, the file with the
    most pose estimates is selected. When multiple files fall within
    ``tiebreak_margin`` of the maximum row count, the most recent by date
    (from the filename) is chosen.

    Arguments
    ---------
    command: Task configuration.
    """
    if not command.root_dir.exists():
        raise FileNotFoundError(
            f"root directory does not exist: {command.root_dir}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )

    deployment_dirs: list[Path] = [
        child
        for child in sorted(command.root_dir.iterdir())
        if child.is_dir() and child.name.endswith(command.deployment_suffix)
    ]
    if not deployment_dirs:
        raise FileNotFoundError(
            f"no deployment directories ending in {command.deployment_suffix!r} "
            f"found under {command.root_dir}"
        )

    groups: dict[str, list[Path]] = {}
    for deployment_dir in deployment_dirs:
        label: str = deployment_dir.name.removesuffix(command.deployment_suffix)
        candidates: list[Path] = sorted(deployment_dir.glob(_POSE_FILE_GLOB))
        if candidates:
            groups[label] = candidates

    if not groups:
        raise FileNotFoundError(
            f"no stereo pose estimate files found in deployment directories "
            f"under {command.root_dir}"
        )

    logger.info(f"found {len(groups)} deployment(s) under {command.root_dir}")

    for deployment, files in sorted(groups.items()):
        selected: Path = _select_file(files, command.tiebreak_margin)
        destination: Path = (
            command.output_dir / f"{deployment}{command.appendix}"
        )
        shutil.copy2(selected, destination)

        row_count: int = _count_data_rows(selected)
        skipped: int = len(files) - 1
        suffix: str = f" ({skipped} candidate(s) skipped)" if skipped else ""
        logger.info(
            f"  {deployment}: {row_count} pose(s) → {destination.name}{suffix}"
        )
