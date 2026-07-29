"""Runtime file manifest for a single ACFR deployment directory."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from afft.utils.log import logger


class DeploymentFiles(BaseModel):
    """
    Validated file manifest for one deployment directory.

    A runtime index of absolute paths, resolved once so that downstream
    parsers and builders never re-walk the deployment tree. It is never
    serialized — it is projected onto a ``DeploymentFileSection`` first.

    Attributes
    ----------
    root: Deployment root directory.
    system_config: SEABED system config; required.
    localizer_config: SEABED localizer config; required.
    magvar_config: Magnetic variation config, or ``None`` if absent.
    mission_log: Mission log, or ``None`` if absent.
    raw_messages: Raw telemetry logs.
    usbl_logs: Topside USBL text logs.
    camera_calibrations: Camera calibration files.
    camera_poses: Stereo pose estimates.
    other: Every file under the root that no role matched.
    """

    model_config = ConfigDict(frozen=True)

    root: Path
    system_config: Path
    localizer_config: Path
    magvar_config: Path | None
    mission_log: Path | None
    raw_messages: list[Path]
    usbl_logs: list[Path]
    camera_calibrations: list[Path]
    camera_poses: list[Path]
    other: list[Path]


# Role -> glob pattern, relative to the deployment root. Ordered: a file is
# assigned to the first role whose pattern matches it, and every file that no
# pattern matches lands in `other`.
_ROLE_PATTERNS: dict[str, str] = {
    "raw_messages": "messages/*.RAW.auv",
    "system_config": "messages/*.SEABED.syscfg",
    "localizer_config": "messages/*.SEABED.localiser.cfg",
    "magvar_config": "messages/*.magnetic_variation.cfg",
    "mission_log": "messages/*.log",
    "camera_calibrations": "camera_calibration/**/*.calib",
    "camera_poses": "camera_poses/**/*stereo_pose_est.data",
    "usbl_logs": "usbl/log-*.txt",
}


def collect_deployment_files(root: Path) -> DeploymentFiles:
    """
    Scan a deployment directory and assign every file to a role.

    Arguments
    ---------
    root: Deployment root directory.

    Returns
    -------
    Validated file manifest for the deployment.

    Raises
    ------
    NotADirectoryError: If the root is not an existing directory.
    ValueError: If a required singular role matches no file or more than one.
    """
    if not root.is_dir():
        raise NotADirectoryError(f"not a deployment directory: {root}")

    matches: dict[str, list[Path]] = {
        role: [] for role in _ROLE_PATTERNS.keys()
    }
    assigned: set[Path] = set()
    for role, pattern in _ROLE_PATTERNS.items():
        for path in root.glob(pattern):
            if not path.is_file() or path in assigned:
                continue
            matches[role].append(path)
            assigned.add(path)

    for role in matches:
        matches[role].sort()

    other: list[Path] = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path not in assigned
    )
    if other:
        logger.warning(
            f"{len(other)} uncategorized file(s) in {root.name}: "
            f"{', '.join(str(path.relative_to(root)) for path in other)}"
        )

    return DeploymentFiles(
        root=root,
        system_config=_required_singular(matches, "system_config", root),
        localizer_config=_required_singular(matches, "localizer_config", root),
        magvar_config=_optional_singular(matches, "magvar_config", root),
        mission_log=_optional_singular(matches, "mission_log", root),
        raw_messages=matches["raw_messages"],
        usbl_logs=matches["usbl_logs"],
        camera_calibrations=matches["camera_calibrations"],
        camera_poses=matches["camera_poses"],
        other=other,
    )


def _required_singular(
    matches: dict[str, list[Path]],
    role: str,
    root: Path,
) -> Path:
    """Resolve a role that must match exactly one file, else raise."""
    paths: list[Path] = matches[role]
    if len(paths) != 1:
        raise ValueError(
            f"expected exactly one {role} in {root.name}, found {len(paths)}"
        )
    return paths[0]


def _optional_singular(
    matches: dict[str, list[Path]],
    role: str,
    root: Path,
) -> Path | None:
    """Resolve a role that may match no file, warning on absence or excess."""
    paths: list[Path] = matches[role]
    if not paths:
        logger.warning(f"no {role} in {root.name}")
        return None
    if len(paths) > 1:
        logger.warning(
            f"{len(paths)} {role} files in {root.name}, using {paths[0].name}"
        )
    return paths[0]
