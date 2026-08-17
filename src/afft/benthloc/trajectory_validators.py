"""Validators for the Benthloc trajectory ingestion file builder."""

import geopandas as gpd

from afft.utils.log import logger

from .common_validators import (
    check_crs_is_wgs84,
    check_geometry_is_point_z,
    check_positions_valid_geodetic,
    check_timestamps_monotonically_increasing,
    check_timestamps_tz_aware_utc,
)
from .trajectory_types import BuildTrajectoryIngestionFileCommand


def check_required_columns_present(
    frame: gpd.GeoDataFrame,
    command: BuildTrajectoryIngestionFileCommand,
) -> None:
    """
    Assert the source geoframe carries every column the builder needs.

    Arguments
    ---------
    frame: Source geoframe to check.
    command: Task command, naming the columns to look for.

    Raises
    ------
    KeyError: If a required column is absent.
    """
    required: set[str] = {
        command.timestamp_column,
        command.yaw_column,
        command.pitch_column,
        command.roll_column,
    }
    missing: list[str] = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(
            f"source geoframe at {command.key!r} is missing columns: {missing}"
        )


def drop_incomplete_rows(
    frame: gpd.GeoDataFrame,
    command: BuildTrajectoryIngestionFileCommand,
) -> tuple[gpd.GeoDataFrame, int]:
    """
    Drop rows with a null position, attitude, or timestamp.

    Warns rather than failing outright -- a source geoframe with a handful
    of unresolved poses is common, and the rest of the trajectory is still
    worth writing.

    Arguments
    ---------
    frame: Source geoframe, already checked for the required columns.
    command: Task command, naming the columns to check for nulls.

    Returns
    -------
    The frame with incomplete rows removed, and how many were dropped.
    """
    attitude_columns: list[str] = [
        command.yaw_column,
        command.pitch_column,
        command.roll_column,
    ]
    complete = (
        frame.geometry.notna()
        & frame[command.timestamp_column].notna()
        & frame[attitude_columns].notna().all(axis=1)
    )
    dropped: int = int((~complete).sum())
    if dropped:
        logger.warning(
            f"dropping {dropped} row(s) with a null position, attitude, or "
            f"timestamp from {command.key!r}"
        )
    return frame.loc[complete].copy(), dropped


def validate_trajectory_geoframe(
    frame: gpd.GeoDataFrame,
    command: BuildTrajectoryIngestionFileCommand,
) -> tuple[gpd.GeoDataFrame, int]:
    """
    Validate and clean the source trajectory geoframe against every
    constraint Benthloc's trajectory ingestion file requires.

    Arguments
    ---------
    frame: Source trajectory geoframe, as read from the bundle.
    command: Task command, naming the columns to validate.

    Returns
    -------
    The frame with incomplete rows dropped and rows sorted by timestamp,
    and how many rows were dropped.

    Raises
    ------
    KeyError: If a required column is absent.
    ValueError: If no poses remain after dropping incomplete rows, the CRS
        is not EPSG:4326, the geometry is not Point Z, a position is
        outside valid WGS-84 ranges, the timestamp column is not tz-aware
        UTC, or timestamps are not monotonically increasing once sorted
        (i.e. the timestamp column has duplicate values).
    """
    check_required_columns_present(frame, command)

    cleaned, dropped = drop_incomplete_rows(frame, command)
    if len(cleaned) == 0:
        raise ValueError(
            f"no poses remain at {command.key!r} after dropping rows with "
            f"a null position, attitude, or timestamp"
        )

    cleaned = cleaned.sort_values(command.timestamp_column).reset_index(
        drop=True
    )

    check_crs_is_wgs84(cleaned)
    check_geometry_is_point_z(cleaned)
    check_positions_valid_geodetic(cleaned)
    check_timestamps_tz_aware_utc(cleaned[command.timestamp_column])
    check_timestamps_monotonically_increasing(cleaned[command.timestamp_column])

    return cleaned, dropped
