"""Tests for Renav coordinate transforms."""

import pandas as pd
import pytest

from afft.renav.transforms import swap_coordinates


def _make_cameras(
    latitudes: list[float], longitudes: list[float]
) -> pd.DataFrame:
    return pd.DataFrame({"latitude": latitudes, "longitude": longitudes})


def test_swap_coordinates_exchanges_columns() -> None:
    cameras = _make_cameras([148.34, 148.35], [-41.25, -41.26])
    result = swap_coordinates(cameras)
    assert list(result["latitude"]) == pytest.approx([-41.25, -41.26])
    assert list(result["longitude"]) == pytest.approx([148.34, 148.35])


def test_swap_coordinates_does_not_mutate_input() -> None:
    cameras = _make_cameras([148.34, 148.35], [-41.25, -41.26])
    original_lat = list(cameras["latitude"])
    swap_coordinates(cameras)
    assert list(cameras["latitude"]) == pytest.approx(original_lat)
