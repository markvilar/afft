"""Collector functions for the collect deployment info task."""

import re

from datetime import datetime
from pathlib import Path

from .types import CollectDeploymentInfoConfig, CollectDeploymentInfoDiagnostics


_LOG_MISSION_PATTERN = re.compile(r"Mission File\s*:\s*(.+?)\.mp\b")
_LOG_CAMPAIGN_PATTERN = re.compile(r"Campaign Dir:\s*(.+)")
_LOG_TIMESTAMP_PATTERN = re.compile(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})")
_MAG_VAR_LAT_PATTERN = re.compile(r"^MAG_VAR_LAT\s+([-\d.]+)")
_MAG_VAR_LNG_PATTERN = re.compile(r"^MAG_VAR_LNG\s+([-\d.]+)")
_MAG_VAR_DEG_PATTERN = re.compile(r"^MAGNETIC_VAR_DEG\s+([-\d.]+)")
_TOPIC_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*):")


def collect_acfr_deployment_label(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> str:
    """
    Collect the ACFR deployment label from the mission log file.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Mission file stem (e.g. ``"rottnest_03_25m_s_out"``), or empty string if
    not found.
    """
    log_file: Path | None = _find_log_file(directory)
    if log_file is None:
        diagnostics.warning(f"no log file found in {directory.name}")
        return ""
    for line in log_file.open():
        match: re.Match[str] | None = _LOG_MISSION_PATTERN.search(line)
        if match:
            return match.group(1).strip()
    diagnostics.warning(f"no mission file entry in {log_file.name}")
    return ""


def collect_acfr_campaign_label(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> str:
    """
    Collect the campaign identifier from the mission log file.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Campaign directory name (e.g. ``"WA201705"``), or empty string if not
    found.
    """
    log_file: Path | None = _find_log_file(directory)
    if log_file is None:
        return ""
    for line in log_file.open():
        match: re.Match[str] | None = _LOG_CAMPAIGN_PATTERN.search(line)
        if match:
            return match.group(1).strip().removeprefix("./")
    return ""


def collect_start_datetime(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> datetime:
    """
    Collect the deployment start datetime from the mission log file.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Datetime of the first log entry.

    Raises
    ------
    ValueError: If no log file or no timestamp line is found.
    """
    log_file: Path | None = _find_log_file(directory)
    if log_file is None:
        raise ValueError(f"no log file found in {directory.name}")
    for line in log_file.open():
        match: re.Match[str] | None = _LOG_TIMESTAMP_PATTERN.match(line)
        if match:
            return datetime.strptime(match.group(1), "%Y/%m/%d %H:%M:%S")
    raise ValueError(f"no timestamp line found in {log_file.name}")


def collect_origin_latitude(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> float:
    """
    Collect the deployment origin latitude from the magnetic variation config.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Latitude in decimal degrees, or ``0.0`` if not found.
    """
    cfg_file: Path | None = _find_magnetic_variation_cfg(directory)
    if cfg_file is None:
        diagnostics.warning(f"no magnetic_variation.cfg in {directory.name}")
        return 0.0
    for line in cfg_file.open():
        match: re.Match[str] | None = _MAG_VAR_LAT_PATTERN.match(line)
        if match:
            return float(match.group(1))
    return 0.0


def collect_origin_longitude(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> float:
    """
    Collect the deployment origin longitude from the magnetic variation config.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Longitude in decimal degrees, or ``0.0`` if not found.
    """
    cfg_file: Path | None = _find_magnetic_variation_cfg(directory)
    if cfg_file is None:
        return 0.0
    for line in cfg_file.open():
        match: re.Match[str] | None = _MAG_VAR_LNG_PATTERN.match(line)
        if match:
            return float(match.group(1))
    return 0.0


def collect_magnetic_variation(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> float:
    """
    Collect the magnetic variation from the magnetic variation config.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Magnetic variation in degrees, or ``0.0`` if not found.
    """
    cfg_file: Path | None = _find_magnetic_variation_cfg(directory)
    if cfg_file is None:
        return 0.0
    for line in cfg_file.open():
        match: re.Match[str] | None = _MAG_VAR_DEG_PATTERN.match(line)
        if match:
            return float(match.group(1))
    return 0.0


def collect_message_topics(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> list[str]:
    """
    Collect the unique message topic names from all RAW AUV log files.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Sorted list of topic names (e.g. ``["RDI", "VIS"]``).
    """
    topics: set[str] = set()
    for raw_file in sorted((directory / "messages").glob("*.RAW.auv")):
        for line in raw_file.open(errors="replace"):
            match: re.Match[str] | None = _TOPIC_PATTERN.match(line)
            if match:
                topics.add(match.group(1))
    return sorted(topics)


def collect_renav_labels(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> list[str]:
    """
    Collect the renav run labels from the camera poses directory.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Sorted list of renav labels (e.g. ``["renav20170523",
    "renav20170524_nousbl"]``).
    """
    labels: list[str] = []
    for data_file in sorted(
        (directory / "camera_poses").glob("*_stereo_pose_est.data")
    ):
        labels.append(data_file.stem.removesuffix("_stereo_pose_est"))
    return labels


def collect_camera_calibration_files(
    directory: Path,
    config: CollectDeploymentInfoConfig,
    diagnostics: CollectDeploymentInfoDiagnostics,
) -> list[str]:
    """
    Collect the camera calibration filenames from the calibration directory.

    Arguments
    ---------
    directory: Deployment root directory.
    config: Task configuration.
    diagnostics: Diagnostics collector for non-fatal issues.

    Returns
    -------
    Sorted list of unique ``.calib`` filenames.
    """
    names: set[str] = set()
    for calib_file in (directory / "camera_calibration").rglob("*.calib"):
        names.add(calib_file.name)
    return sorted(names)


def _find_log_file(directory: Path) -> Path | None:
    log_files: list[Path] = sorted((directory / "messages").glob("*.log"))
    return log_files[0] if log_files else None


def _find_magnetic_variation_cfg(directory: Path) -> Path | None:
    cfg_files: list[Path] = sorted(
        (directory / "messages").glob("*.magnetic_variation.cfg")
    )
    return cfg_files[0] if cfg_files else None
