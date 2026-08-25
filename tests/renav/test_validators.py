"""Tests for Renav position validators."""

import pandas as pd

from afft.renav.validators import (
    check_valid_latitudes,
    check_valid_longitudes,
    check_valid_positions_geodetic,
)


def _make_cameras(
    latitudes: list[float], longitudes: list[float]
) -> pd.DataFrame:
    return pd.DataFrame({"latitude": latitudes, "longitude": longitudes})


def test_check_valid_latitudes_valid() -> None:
    cameras = _make_cameras([-41.25, -41.26], [148.34, 148.35])
    assert check_valid_latitudes(cameras) is True


def test_check_valid_latitudes_invalid() -> None:
    cameras = _make_cameras([148.34, 148.35], [-41.25, -41.26])
    assert check_valid_latitudes(cameras) is False


def test_check_valid_longitudes_valid() -> None:
    cameras = _make_cameras([-41.25, -41.26], [148.34, 148.35])
    assert check_valid_longitudes(cameras) is True


def test_check_valid_longitudes_invalid() -> None:
    cameras = _make_cameras([-41.25, -41.26], [200.0, 201.0])
    assert check_valid_longitudes(cameras) is False


def test_check_valid_positions_geodetic_valid() -> None:
    cameras = _make_cameras([-41.25, -41.26], [148.34, 148.35])
    assert check_valid_positions_geodetic(cameras) is True


def test_check_valid_positions_geodetic_invalid_latitude() -> None:
    cameras = _make_cameras([148.34, 148.35], [-41.25, -41.26])
    assert check_valid_positions_geodetic(cameras) is False


def test_check_valid_positions_geodetic_invalid_longitude() -> None:
    cameras = _make_cameras([-41.25, -41.26], [200.0, 201.0])
    assert check_valid_positions_geodetic(cameras) is False
