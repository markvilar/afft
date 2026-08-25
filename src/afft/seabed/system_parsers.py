"""Parser for the raw SEABED vehicle system config (``*.SEABED.syscfg``)."""

from pathlib import Path

from afft.io import read_lines
from afft.utils.log import logger

from .system_types import (
    LoggerConfig,
    SeabedSystemConfig,
    SensorConfig,
    SensorEntry,
    VehicleInfo,
)

type Block = tuple[str, list[str]]

KNOWN_BLOCKS: frozenset[str] = frozenset({"syscfg", "sensors", "logger"})


def parse_system_config(path: Path) -> SeabedSystemConfig:
    """
    Parses a raw SEABED system config file into a typed structure.

    Only the ``syscfg``, ``sensors``, and ``logger`` blocks are modeled;
    other blocks are skipped. A missing or duplicated known block raises
    ``ValueError``.

    Arguments
    ---------
    path: Path to a ``*.SEABED.syscfg`` file.

    Returns
    -------
    The parsed SeabedSystemConfig.
    """
    blocks = _extract_blocks(read_lines(path))

    skipped = [name for name, _ in blocks if name not in KNOWN_BLOCKS]
    if skipped:
        logger.debug(f"skipped unmodeled syscfg blocks: {skipped}")

    return SeabedSystemConfig(
        vehicle=_parse_syscfg(_require_block(blocks, "syscfg")),
        sensors=_parse_sensors(_require_block(blocks, "sensors")),
        logger=_parse_logger(_require_block(blocks, "logger")),
    )


def _strip_comment(line: str) -> str:
    """Strips an inline or full-line ``#`` comment and surrounding space."""
    return line.split("#", 1)[0].strip()


def _extract_blocks(lines: list[str]) -> list[Block]:
    """
    Splits the file into ``BEGIN: <name>`` … ``END: <name>`` blocks.

    Comments and blank lines are stripped before each block body is
    collected.
    """
    blocks: list[Block] = []
    name: str | None = None
    body: list[str] = []

    for raw in lines:
        line = _strip_comment(raw)
        if not line:
            continue
        if line.startswith("BEGIN:"):
            name = line[len("BEGIN:") :].strip()
            body = []
        elif line.startswith("END:"):
            if name is not None:
                blocks.append((name, body))
            name = None
        elif name is not None:
            body.append(line)

    return blocks


def _require_block(blocks: list[Block], name: str) -> list[str]:
    """Returns the body of the single block ``name``, else raises."""
    bodies = [body for block_name, body in blocks if block_name == name]
    if len(bodies) != 1:
        raise ValueError(
            f"expected exactly one '{name}' block, found {len(bodies)}"
        )
    return bodies[0]


def _parse_key_values(body: list[str]) -> dict[str, str]:
    """Parses ``key: value`` lines into a mapping, ignoring the rest."""
    values: dict[str, str] = {}
    for line in body:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def _parse_syscfg(body: list[str]) -> VehicleInfo:
    """Parses the ``syscfg`` block into a VehicleInfo."""
    values = _parse_key_values(body)
    return VehicleInfo(
        vehicle_name=values["vehicle_name"],
        vehicle_config=values["vehicle_cfg"],
    )


def _parse_sensors(body: list[str]) -> SensorConfig:
    """Parses the ``sensors`` block roster into a SensorConfig."""
    entries: list[SensorEntry] = []
    for line in body:
        fields = line.split()
        if len(fields) < 4:
            continue
        entries.append(
            SensorEntry(
                name=fields[0],
                driver=fields[1],
                transport=fields[3],
            )
        )
    return SensorConfig(entries=entries)


def _parse_logger(body: list[str]) -> LoggerConfig:
    """Parses the ``logger`` block into a LoggerConfig."""
    values = _parse_key_values(body)
    streams = [
        stream.strip()
        for stream in values["log_to_disk"].split(",")
        if stream.strip()
    ]
    return LoggerConfig(log_dir=values["log_dir"], logged_streams=streams)
