"""Parser for the LinkQuest TrackLink USBL raw log format."""

import dataclasses
import re

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from afft.utils.log import logger

from .types import TrackLinkFixEntry, TrackLinkRawEntry


_FIX_RE: re.Pattern[str] = re.compile(
    r"^USBL_FIX:\s+(?P<timestamp>\S+)"
    r"\s+X:(?P<ship_latitude>\S+)\s+Y:(?P<ship_longitude>\S+)"
    r"\s+hdg:(?P<ship_heading>\S+)\s+roll:(?P<ship_roll>\S+)\s+pitch:(?P<ship_pitch>\S+)"
    r"\s+bear:(?P<target_bearing_angle>\S+)\s+rng:(?P<target_slant_range>\S+)"
)

_RAW_RE: re.Pattern[str] = re.compile(
    r"^USBL_RAW:\s+(?P<timestamp>\S+)"  # timestamp
    r"(?:\s+(?P<flag1>\d+))?"  # optional flag1 (absent on first ping)
    r"\s+\d+:\d+:\d+"  # HH:MM:SS (skip)
    r"\s+(?P<flag2>\S+)"  # flag2
    r"(?:\s+\S+){2}"  # bearing, range (skip)
    r"\s+(?P<log_x>\S+)\s+(?P<log_y>\S+)\s+(?P<log_z>\S+)"  # XYZ as logged (X/Y swapped)
)


def parse_fix_entries(path: Path) -> pd.DataFrame:
    """Parse USBL_FIX lines from a TrackLink log file.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: unix_timestamp, ship_latitude, ship_longitude,
    ship_heading, ship_roll, ship_pitch, target_bearing_angle,
    target_slant_range.
    """
    entries: list[TrackLinkFixEntry] = []

    with open(path) as file:
        for line in file:
            if not line.startswith("USBL_FIX:"):
                continue
            entry: TrackLinkFixEntry | None = _parse_fix_line(line)
            if entry is None:
                continue
            entries.append(entry)

    dataframe: pd.DataFrame = pd.DataFrame(
        [dataclasses.asdict(entry) for entry in entries]
    )
    if not dataframe.empty:
        dataframe["timestamp"] = dataframe["unix_timestamp"].apply(_unix_to_iso)
    return dataframe


def parse_raw_entries(path: Path) -> pd.DataFrame:
    """Parse USBL_RAW lines from a TrackLink log file.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: unix_timestamp, flag1, flag2, target_x,
    target_y, target_z.
    """
    entries: list[TrackLinkRawEntry] = []

    with open(path) as file:
        for line in file:
            if not line.startswith("USBL_RAW:"):
                continue
            entry: TrackLinkRawEntry | None = _parse_raw_line(line)
            if entry is None:
                continue
            entries.append(entry)

    return pd.DataFrame([dataclasses.asdict(entry) for entry in entries])


def parse_novatel_entries(path: Path) -> pd.DataFrame:
    """Parse NOVATEL INS lines from a TrackLink log file.

    Only lines with the positional data format are parsed (those whose third
    token is exactly `<`). Header-type NOVATEL lines (`<INSPVA ...`) are
    skipped.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: unix_timestamp, ship_latitude, ship_longitude.
    """
    records: list[dict[str, object]] = []

    with open(path) as file:
        for line in file:
            if not line.startswith("NOVATEL:"):
                continue
            parsed: tuple[float, float, float] | None = _parse_novatel_line(
                line
            )
            if parsed is None:
                continue
            unix_ts: float
            ship_lat: float
            ship_lon: float
            unix_ts, ship_lat, ship_lon = parsed
            records.append(
                {
                    "unix_timestamp": unix_ts,
                    "ship_latitude": ship_lat,
                    "ship_longitude": ship_lon,
                }
            )

    return pd.DataFrame(records)


def parse_tracklink_log(path: Path) -> pd.DataFrame:
    """Parse a TrackLink USBL log file into a merged DataFrame.

    Parses USBL_FIX and USBL_RAW entries and merges them on timestamp.
    USBL_FIX is the primary table. RAW columns are matched via
    nearest-timestamp join (tolerance 1 s); columns are NaN when no match
    exists.

    The `target_bearing_angle` column contains the compass-referenced azimuth
    as stored by the TrackLink system (degrees from North, clockwise), already
    incorporating ship heading from the INS.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: timestamp, ship_latitude, ship_longitude,
    ship_heading, ship_roll, ship_pitch, target_bearing_angle,
    target_slant_range, flag1, flag2, target_x, target_y, target_z.
    """
    fix: pd.DataFrame = parse_fix_entries(path)
    raw: pd.DataFrame = parse_raw_entries(path)

    if fix.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "ship_latitude",
                "ship_longitude",
                "ship_heading",
                "ship_roll",
                "ship_pitch",
                "target_bearing_angle",
                "target_slant_range",
                "flag1",
                "flag2",
                "target_x",
                "target_y",
                "target_z",
            ]
        )

    fix_sorted: pd.DataFrame = fix.sort_values("unix_timestamp")

    if raw.empty:
        logger.warning(
            f"{path.name}: no USBL_RAW entries — "
            f"target_x, target_y, target_z will be NaN"
        )
        fix_sorted["flag1"] = float("nan")
        fix_sorted["flag2"] = float("nan")
        fix_sorted["target_x"] = float("nan")
        fix_sorted["target_y"] = float("nan")
        fix_sorted["target_z"] = float("nan")
    else:
        fix_sorted = pd.merge_asof(
            fix_sorted,
            raw.sort_values("unix_timestamp"),
            on="unix_timestamp",
            direction="nearest",
            tolerance=1.0,
        )

    column_order: list[str] = [
        "timestamp",
        "ship_latitude",
        "ship_longitude",
        "ship_heading",
        "ship_roll",
        "ship_pitch",
        "target_bearing_angle",
        "target_slant_range",
        "flag1",
        "flag2",
        "target_x",
        "target_y",
        "target_z",
    ]
    return (
        fix_sorted.drop(columns=["unix_timestamp"])
        .reindex(columns=column_order)
        .reset_index(drop=True)
    )


def _parse_fix_line(line: str) -> TrackLinkFixEntry | None:
    """Parse a single USBL_FIX line into a TrackLinkFixEntry."""
    match: re.Match[str] | None = _FIX_RE.match(line)
    if match is None:
        return None
    return TrackLinkFixEntry(
        unix_timestamp=float(match["timestamp"]),
        ship_latitude=float(match["ship_latitude"]),
        ship_longitude=float(match["ship_longitude"]),
        ship_heading=float(match["ship_heading"]),
        ship_roll=float(match["ship_roll"]),
        ship_pitch=float(match["ship_pitch"]),
        target_bearing_angle=float(match["target_bearing_angle"]),
        target_slant_range=float(match["target_slant_range"]),
    )


def _parse_raw_line(line: str) -> TrackLinkRawEntry | None:
    """Parse a single USBL_RAW line into a TrackLinkRawEntry."""
    match: re.Match[str] | None = _RAW_RE.match(line)
    if match is None:
        return None
    flag1_str: str | None = match["flag1"]
    return TrackLinkRawEntry(
        unix_timestamp=float(match["timestamp"]),
        flag1=int(flag1_str) if flag1_str is not None else None,
        flag2=int(match["flag2"]),
        target_x=float(match["log_y"]),  # TrackLink logs X and Y swapped
        target_y=float(match["log_x"]),
        target_z=float(match["log_z"]),
    )


def _parse_novatel_line(
    line: str,
) -> tuple[float, float, float] | None:
    """Extract (unix_timestamp, ship_latitude, ship_longitude) from a NOVATEL line.

    Skips header-type lines whose third token is not exactly `<`.

    Format (whitespace-separated):
        NOVATEL:  <timestamp>  <  <count>  <gps_time>  <lat>  <lon>  ...
    """
    parts: list[str] = line.split()
    if len(parts) < 7 or parts[2] != "<":
        return None
    try:
        return (float(parts[1]), float(parts[5]), float(parts[6]))
    except ValueError:
        return None


def _unix_to_iso(unix_seconds: float) -> str:
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).isoformat()
