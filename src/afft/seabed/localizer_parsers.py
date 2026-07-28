"""Parser for the raw SEABED localizer config (``*.SEABED.localiser.cfg``)."""

from pathlib import Path

from afft.io import read_lines

from .localizer_types import (
    AuvSensorConfig,
    Origin,
    SeabedLocalizerConfig,
    SensorPoseEntry,
    ShipSensorConfig,
)

type Entry = tuple[str, str]

AUV_BANNER: str = "AUV Sensor Configuration"
SHIP_BANNER: str = "Ship Sensor Configuration"

ORIGIN_KEYS: tuple[str, str] = ("LATITUDE", "LONGITUDE")

# Maps a ``<NAME>_POSE_<SUFFIX>`` suffix to the SensorPoseEntry field.
POSE_COMPONENTS: dict[str, str] = {
    "X": "locx",
    "Y": "locy",
    "Z": "locz",
    "PHI": "rotx",
    "THETA": "roty",
    "PSI": "rotz",
}


def parse_localizer_config(path: Path) -> SeabedLocalizerConfig:
    """
    Parses a raw SEABED localizer config file into a typed structure.

    Only the geodetic origin and the AUV / ship sensor extrinsic poses are
    modeled; the EKF-tuning bulk is read past and ignored. The two section
    banners partition the tail of the file into the AUV and ship regions.

    Arguments
    ---------
    path: Path to a ``*.SEABED.localiser.cfg`` file.

    Returns
    -------
    The parsed SeabedLocalizerConfig.
    """
    lines = read_lines(path)

    auv_index = _find_banner(lines, AUV_BANNER)
    ship_index = _find_banner(lines, SHIP_BANNER)
    active_keys = {key for key, _ in _iter_entries(lines)}

    missing: list[str] = []
    if auv_index is None:
        missing.append(AUV_BANNER)
    if ship_index is None:
        missing.append(SHIP_BANNER)
    for key in ORIGIN_KEYS:
        if key not in active_keys:
            missing.append(key)
    if missing:
        raise ValueError(
            f"missing required localizer config elements: {', '.join(missing)}"
        )

    assert auv_index is not None and ship_index is not None
    if auv_index >= ship_index:
        raise ValueError(
            "AUV sensor banner must precede the ship sensor banner"
        )

    return SeabedLocalizerConfig(
        origin=_parse_origin(lines[:auv_index]),
        auv_sensors=AuvSensorConfig(
            sensor_poses=_parse_poses(lines[auv_index:ship_index])
        ),
        ship_sensors=ShipSensorConfig(
            sensor_poses=_parse_poses(lines[ship_index:])
        ),
    )


def _strip_comment(line: str) -> str:
    """Strips an inline or full-line ``#`` comment and surrounding space."""
    return line.split("#", 1)[0].strip()


def _iter_entries(lines: list[str]) -> list[Entry]:
    """
    Yields ``(key, value)`` for each active line.

    The value is the first whitespace token after the key; inline ``#…``
    comments (including commented-out alternate values) are stripped first.
    Comment-only and blank lines yield nothing.
    """
    entries: list[Entry] = []
    for line in lines:
        fields = _strip_comment(line).split()
        if len(fields) < 2:
            continue
        entries.append((fields[0], fields[1]))
    return entries


def _find_banner(lines: list[str], banner: str) -> int | None:
    """Returns the index of the first comment line containing ``banner``."""
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#") and banner in line:
            return index
    return None


def _match_pose(key: str) -> tuple[str, str] | None:
    """
    Splits a pose key into ``(name, field)`` or returns ``None``.

    A pose key matches ``<NAME>_POSE_<SUFFIX>`` where ``<SUFFIX>`` is one of
    the six pose components; ``field`` is the SensorPoseEntry attribute name.
    """
    parts = key.split("_POSE_")
    if len(parts) != 2 or parts[1] not in POSE_COMPONENTS:
        return None
    return parts[0], POSE_COMPONENTS[parts[1]]


def _parse_origin(lines: list[str]) -> Origin:
    """
    Parses the geodetic origin from the origin region.

    Operators leave several site presets active; the effective origin is the
    last active ``LATITUDE`` / ``LONGITUDE`` (sequential-reader semantics —
    later assignment overwrites), matching the true deployment origin.
    """
    found: dict[str, float] = {}
    for key, value in _iter_entries(lines):
        if key in ORIGIN_KEYS:
            found[key] = float(value)
    return Origin(latitude=found["LATITUDE"], longitude=found["LONGITUDE"])


def _parse_poses(lines: list[str]) -> list[SensorPoseEntry]:
    """
    Groups ``<NAME>_POSE_*`` families within a region into pose entries.

    Missing translation/rotation components are zero-filled. A duplicated
    active component within a family raises ``ValueError``.
    """
    components: dict[str, dict[str, float]] = {}
    order: list[str] = []
    for key, value in _iter_entries(lines):
        match = _match_pose(key)
        if match is None:
            continue
        name, field = match
        if name not in components:
            components[name] = {}
            order.append(name)
        if field in components[name]:
            raise ValueError(f"duplicate pose entry: {key}")
        components[name][field] = float(value)

    return [
        SensorPoseEntry(
            label=name.lower(),
            locx=components[name].get("locx", 0.0),
            locy=components[name].get("locy", 0.0),
            locz=components[name].get("locz", 0.0),
            rotx=components[name].get("rotx", 0.0),
            roty=components[name].get("roty", 0.0),
            rotz=components[name].get("rotz", 0.0),
        )
        for name in order
    ]
