"""Parser for the LinkQuest TrackLink USBL raw log format."""

import re

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from afft.utils.log import logger


_FIX_RE: re.Pattern[str] = re.compile(
    r"^USBL_FIX:\s+(\S+)"
    r"\s+X:(\S+)\s+Y:(\S+)"
    r"\s+hdg:(\S+)\s+roll:(\S+)\s+pitch:(\S+)"
    r"\s+bear:(\S+)\s+rng:(\S+)"
)


def parse_fix_entries(path: Path) -> pd.DataFrame:
    """Parse USBL_FIX lines from a TrackLink log file.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: unix_timestamp, timestamp, ship_latitude,
    ship_longitude, ship_heading, ship_roll, ship_pitch,
    target_bearing_angle, target_slant_range.
    """
    records: list[dict[str, object]] = []

    with open(path) as file:
        for line in file:
            if not line.startswith("USBL_FIX:"):
                continue
            match = _FIX_RE.match(line)
            if match is None:
                continue
            ts, lat, lon, heading, roll, pitch, bearing, slant_range = (
                match.groups()
            )
            unix_ts = float(ts)
            records.append(
                {
                    "unix_timestamp": unix_ts,
                    "timestamp": _unix_to_iso(unix_ts),
                    "ship_latitude": float(lat),
                    "ship_longitude": float(lon),
                    "ship_heading": float(heading),
                    "ship_roll": float(roll),
                    "ship_pitch": float(pitch),
                    "target_bearing_angle": float(bearing),
                    "target_slant_range": float(slant_range),
                }
            )

    return pd.DataFrame(records)


def parse_raw_entries(path: Path) -> pd.DataFrame:
    """Parse USBL_RAW lines from a TrackLink log file.

    The east, north, and depth fields are the horizontal NED displacements and
    target depth pre-computed by the TrackLink hardware.

    Arguments
    ---------
    path: Path to the TrackLink log file.

    Returns
    -------
    DataFrame with columns: unix_timestamp, target_x, target_y,
    target_z.
    """
    records: list[dict[str, object]] = []

    with open(path) as file:
        for line in file:
            if not line.startswith("USBL_RAW:"):
                continue
            parsed = _parse_raw_line(line)
            if parsed is None:
                continue
            unix_ts, east, north, depth = parsed
            records.append(
                {
                    "unix_timestamp": unix_ts,
                    "target_x": east,
                    "target_y": north,
                    "target_z": depth,
                }
            )

    return pd.DataFrame(records)


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
            parsed = _parse_novatel_line(line)
            if parsed is None:
                continue
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
    target_slant_range, target_x, target_y, target_z.
    """
    fix = parse_fix_entries(path)
    raw = parse_raw_entries(path)

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
                "target_x",
                "target_y",
                "target_z",
            ]
        )

    fix_sorted = fix.sort_values("unix_timestamp")

    if raw.empty:
        logger.warning(
            f"{path.name}: no USBL_RAW entries — "
            f"target_x, target_y, target_z will be NaN"
        )
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

    column_order = [
        "timestamp",
        "ship_latitude",
        "ship_longitude",
        "ship_heading",
        "ship_roll",
        "ship_pitch",
        "target_bearing_angle",
        "target_slant_range",
        "target_x",
        "target_y",
        "target_z",
    ]
    return (
        fix_sorted.drop(columns=["unix_timestamp"])
        .reindex(columns=column_order)
        .reset_index(drop=True)
    )


def _parse_raw_line(
    line: str,
) -> tuple[float, float, float, float] | None:
    """Extract (unix_timestamp, east, north, depth) from a USBL_RAW line.

    Fields are indexed from the end to handle the optional counter token
    that appears after the timestamp in all but the first ping.

    Format (whitespace-separated):
        USBL_RAW:  <timestamp>  [counter]  <HH:MM:SS>  <flag>
                   <bearing>  <range>  <x>  <y>  <z>  0.0
    """
    parts = line.split()
    if len(parts) < 8:
        return None
    return (
        float(parts[1]),
        float(parts[-4]),
        float(parts[-3]),
        float(parts[-2]),
    )


def _parse_novatel_line(
    line: str,
) -> tuple[float, float, float] | None:
    """Extract (unix_timestamp, ship_latitude, ship_longitude) from a NOVATEL line.

    Skips header-type lines whose third token is not exactly `<`.

    Format (whitespace-separated):
        NOVATEL:  <timestamp>  <  <count>  <gps_time>  <lat>  <lon>  ...
    """
    parts = line.split()
    if len(parts) < 7 or parts[2] != "<":
        return None
    try:
        return (float(parts[1]), float(parts[5]), float(parts[6]))
    except ValueError:
        return None


def _unix_to_iso(unix_seconds: float) -> str:
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).isoformat()
