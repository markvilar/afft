"""Builders mapping parsed deployment inputs onto descriptor sections."""

import re

from pathlib import Path

from afft.deployment import (
    DeploymentFiles,
    DeploymentFileSection,
    DeploymentMetadata,
    DeploymentSystemSection,
    DeploymentTelemetrySection,
)
from afft.seabed import SeabedSystemConfig

from .types import DescribeDeploymentDiagnostics

_LOG_MISSION_PATTERN = re.compile(r"Mission File\s*:\s*(.+?)\.mp\b")
_LOG_CAMPAIGN_PATTERN = re.compile(r"Campaign Dir:\s*(.+)")
_MAG_VAR_LAT_PATTERN = re.compile(r"^MAG_VAR_LAT\s+([-\d.]+)")
_MAG_VAR_LNG_PATTERN = re.compile(r"^MAG_VAR_LNG\s+([-\d.]+)")
_MAG_VAR_DEG_PATTERN = re.compile(r"^MAGNETIC_VAR_DEG\s+([-\d.]+)")
_TOPIC_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*):")


def build_deployment_file_section(
    files: DeploymentFiles,
) -> DeploymentFileSection:
    """
    Project a file manifest onto the descriptor's file inventory.

    Arguments
    ---------
    files: Resolved file manifest for the deployment.

    Returns
    -------
    File inventory with every path relative to the deployment root.
    """

    def relative(paths: list[Path]) -> list[str]:
        return [str(path.relative_to(files.root)) for path in paths]

    def singular(path: Path | None) -> list[str]:
        return relative([path]) if path is not None else []

    return DeploymentFileSection(
        raw_messages=relative(files.raw_messages),
        system_config=singular(files.system_config),
        localizer_config=singular(files.localizer_config),
        magvar_config=singular(files.magvar_config),
        mission_log=singular(files.mission_log),
        camera_calibrations=relative(files.camera_calibrations),
        camera_poses=relative(files.camera_poses),
        usbl_logs=relative(files.usbl_logs),
    )


def build_system_section(
    system_config: SeabedSystemConfig,
) -> DeploymentSystemSection:
    """
    Map a parsed SEABED system config onto the descriptor's system section.

    Arguments
    ---------
    system_config: Parsed SEABED system config.

    Returns
    -------
    The deployment vehicle's identity, logging setup, and sensor labels.
    """
    return DeploymentSystemSection(
        vehicle_name=system_config.vehicle.vehicle_name,
        vehicle_config=system_config.vehicle.vehicle_config,
        log_directory=system_config.logger.log_dir,
        logged_streams=system_config.logger.logged_streams,
        sensors=[entry.name for entry in system_config.sensors.entries],
    )


def build_telemetry_section(
    files: DeploymentFiles,
    deployment_label: str,
    diagnostics: DescribeDeploymentDiagnostics,
) -> DeploymentTelemetrySection:
    """
    Collect the message topics observed in the deployment's RAW AUV logs.

    Arguments
    ---------
    files: Resolved file manifest for the deployment.
    deployment_label: Label of the deployment, used to key warnings.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    The observed message topics, sorted and unique.
    """
    if not files.raw_messages:
        diagnostics.warning(deployment_label, "no RAW.auv files")
        return DeploymentTelemetrySection(topics=[])

    topics: set[str] = set()
    for raw_file in files.raw_messages:
        for line in raw_file.open(errors="replace"):
            match: re.Match[str] | None = _TOPIC_PATTERN.match(line)
            if match:
                topics.add(match.group(1))

    if not topics:
        diagnostics.warning(
            deployment_label,
            f"no message topics in {len(files.raw_messages)} RAW.auv file(s)",
        )
    return DeploymentTelemetrySection(topics=sorted(topics))


def build_deployment_metadata(
    files: DeploymentFiles,
    deployment_label: str,
    diagnostics: DescribeDeploymentDiagnostics,
) -> DeploymentMetadata:
    """
    Collect the deployment's metadata from its mission log and magnetic
    variation config.

    Arguments
    ---------
    files: Resolved file manifest for the deployment.
    deployment_label: Label of the deployment, used to key warnings.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    Collected metadata, with unresolved fields left empty or zero.
    """
    acfr_deployment_label: str = ""
    acfr_campaign_label: str = ""
    if files.mission_log is None:
        diagnostics.warning(deployment_label, "no mission log file")
    else:
        acfr_deployment_label = _search_file(
            files.mission_log, _LOG_MISSION_PATTERN
        )
        if not acfr_deployment_label:
            diagnostics.warning(
                deployment_label,
                f"no mission file entry in {files.mission_log.name}",
            )
        acfr_campaign_label = _search_file(
            files.mission_log, _LOG_CAMPAIGN_PATTERN
        ).removeprefix("./")
        if not acfr_campaign_label:
            diagnostics.warning(
                deployment_label,
                f"no campaign dir entry in {files.mission_log.name}",
            )

    origin_latitude: float = 0.0
    origin_longitude: float = 0.0
    magnetic_variation: float = 0.0
    if files.magvar_config is None:
        diagnostics.warning(deployment_label, "no magnetic variation config")
    else:
        origin_latitude = _match_float(
            files.magvar_config,
            _MAG_VAR_LAT_PATTERN,
            "MAG_VAR_LAT",
            deployment_label,
            diagnostics,
        )
        origin_longitude = _match_float(
            files.magvar_config,
            _MAG_VAR_LNG_PATTERN,
            "MAG_VAR_LNG",
            deployment_label,
            diagnostics,
        )
        magnetic_variation = _match_float(
            files.magvar_config,
            _MAG_VAR_DEG_PATTERN,
            "MAGNETIC_VAR_DEG",
            deployment_label,
            diagnostics,
        )

    return DeploymentMetadata(
        acfr_deployment_label=acfr_deployment_label,
        acfr_campaign_label=acfr_campaign_label,
        acfr_platform_label="",
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        magnetic_variation=magnetic_variation,
    )


def _search_file(path: Path, pattern: re.Pattern[str]) -> str:
    """Return the first capture of a pattern in a file, or an empty string."""
    for line in path.open(errors="replace"):
        match: re.Match[str] | None = pattern.search(line)
        if match:
            return match.group(1).strip()
    return ""


def _match_float(
    path: Path,
    pattern: re.Pattern[str],
    key: str,
    deployment_label: str,
    diagnostics: DescribeDeploymentDiagnostics,
) -> float:
    """
    Return the first float a key-anchored pattern matches in a file.

    Falls back to ``0.0`` and warns: the file is authoritative for the origin,
    so a present-but-unmatched key is a defect rather than a silent default.
    """
    for line in path.open(errors="replace"):
        match: re.Match[str] | None = pattern.match(line)
        if match:
            return float(match.group(1))
    diagnostics.warning(
        deployment_label, f"no {key} entry in {path.name}, using 0.0"
    )
    return 0.0
