"""Validators shared by both Benthloc ingestion file builders."""

import geopandas as gpd
import pandas as pd

from afft.renav import check_valid_positions_geodetic

_WGS84_CRS: str = "EPSG:4326"


def check_crs_is_wgs84(frame: gpd.GeoDataFrame) -> None:
    """
    Assert a geoframe's CRS is EPSG:4326.

    Benthloc's reader silently reprojects a mismatched CRS rather than
    failing, so a wrong upstream CRS must be caught here instead.

    Arguments
    ---------
    frame: Geoframe to check.

    Raises
    ------
    ValueError: If the CRS is unset or is not EPSG:4326.
    """
    if frame.crs is None or frame.crs.to_string() != _WGS84_CRS:
        raise ValueError(f"geoframe CRS must be {_WGS84_CRS}, got {frame.crs}")


def check_geometry_is_point_z(frame: gpd.GeoDataFrame) -> None:
    """
    Assert every geometry in a geoframe is a 3D point.

    A 2D point would surface as an ``AttributeError`` on Benthloc's side
    (``row.geometry.z``) rather than a clear error here.

    Arguments
    ---------
    frame: Geoframe to check.

    Raises
    ------
    ValueError: If any geometry is not a `Point`, or lacks a `z` ordinate.
    """
    if not (frame.geometry.geom_type == "Point").all():
        raise ValueError("geoframe geometry must be Point")
    if not frame.geometry.has_z.all():
        raise ValueError("geoframe geometry must be Point Z (3D)")


def check_positions_valid_geodetic(frame: gpd.GeoDataFrame) -> None:
    """
    Assert every position is within valid WGS-84 ranges.

    Arguments
    ---------
    frame: Geoframe to check.

    Raises
    ------
    ValueError: If any longitude/latitude is outside its valid range.
    """
    positions = pd.DataFrame(
        {"latitude": frame.geometry.y, "longitude": frame.geometry.x}
    )
    if not check_valid_positions_geodetic(positions):
        raise ValueError("geoframe holds positions outside valid WGS-84 ranges")


def check_timestamps_tz_aware_utc(timestamps: pd.Series) -> None:
    """
    Assert a timestamp column is timezone-aware UTC.

    Naive timestamps are not assumed UTC -- Benthloc's reader rejects them
    outright, so this builder does too.

    Arguments
    ---------
    timestamps: Timestamp column to check.

    Raises
    ------
    ValueError: If the column is not a datetime column, is timezone-naive,
        or its timezone is not UTC.
    """
    if not pd.api.types.is_datetime64_any_dtype(timestamps):
        raise ValueError(f"{timestamps.name!r} column is not a datetime column")
    if timestamps.dt.tz is None:
        raise ValueError(
            f"{timestamps.name!r} column is timezone-naive; a tz-aware UTC "
            f"column is required"
        )
    if str(timestamps.dt.tz) != "UTC":
        raise ValueError(
            f"{timestamps.name!r} column timezone is {timestamps.dt.tz}, "
            f"expected UTC"
        )


def check_timestamps_monotonically_increasing(timestamps: pd.Series) -> None:
    """
    Assert a timestamp column is monotonically increasing.

    Arguments
    ---------
    timestamps: Timestamp column to check.

    Raises
    ------
    ValueError: If the column is not monotonically increasing.
    """
    if not timestamps.is_monotonic_increasing:
        raise ValueError(
            f"{timestamps.name!r} column is not monotonically increasing"
        )
