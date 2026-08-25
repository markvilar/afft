"""Validators for Renav navigation data."""

import pandas as pd


_LATITUDE_MIN: float = -90.0
_LATITUDE_MAX: float = 90.0
_LONGITUDE_MIN: float = -180.0
_LONGITUDE_MAX: float = 180.0


def check_valid_latitudes(cameras: pd.DataFrame) -> bool:
    """
    Return True if all ``latitude`` values are within [-90, 90].

    Arguments
    ---------
    cameras: DataFrame containing a ``latitude`` column.

    Returns
    -------
    True if all values are in the valid range, False otherwise.
    """
    return bool(cameras["latitude"].between(_LATITUDE_MIN, _LATITUDE_MAX).all())


def check_valid_longitudes(cameras: pd.DataFrame) -> bool:
    """
    Return True if all ``longitude`` values are within [-180, 180].

    Arguments
    ---------
    cameras: DataFrame containing a ``longitude`` column.

    Returns
    -------
    True if all values are in the valid range, False otherwise.
    """
    return bool(
        cameras["longitude"].between(_LONGITUDE_MIN, _LONGITUDE_MAX).all()
    )


def check_valid_positions_geodetic(cameras: pd.DataFrame) -> bool:
    """
    Return True if all geodetic positions are within valid WGS-84 ranges.

    Checks that ``latitude`` is in [-90, 90] and ``longitude`` is in
    [-180, 180].

    Arguments
    ---------
    cameras: DataFrame containing ``latitude`` and ``longitude`` columns.

    Returns
    -------
    True if both columns are valid, False otherwise.
    """
    return check_valid_latitudes(cameras) and check_valid_longitudes(cameras)
