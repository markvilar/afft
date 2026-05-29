"""Tests for the USBL position resolution processor."""

import math

import pandas as pd
import pytest

from afft.sensors.usbl_linkquest import (
    UsblResolvePositionConfig,
    resolve_usbl_position,
)

_EARTH_RADIUS_M = 6_371_000.0


def _usbl_row(
    timestamp: str,
    ship_lat: float,
    ship_lon: float,
    heading: float,
    bearing: float,
    range_m: float,
) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "ship_latitude": ship_lat,
        "ship_longitude": ship_lon,
        "ship_heading": heading,
        "ship_roll": 0.0,
        "ship_pitch": 0.0,
        "target_bearing": bearing,
        "target_slant_range": range_m,
    }


def _usbl_df(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _pressure_df(timestamps: list[str], depths: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"timestamp": timestamps, "depth": depths})


def test_output_columns() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [5.0, 5.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    for col in (
        "target_depth",
        "horizontal_range",
        "target_latitude",
        "target_longitude",
    ):
        assert col in result.columns


def test_zero_depth_horizontal_range_equals_slant_range() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    assert math.isclose(
        result["horizontal_range"].iloc[0], 1000.0, rel_tol=1e-9
    )


def test_projection_east_from_equator() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    expected_lon = math.degrees(1000.0 / _EARTH_RADIUS_M)
    assert math.isclose(result["target_latitude"].iloc[0], 0.0, abs_tol=1e-6)
    assert math.isclose(
        result["target_longitude"].iloc[0], expected_lon, rel_tol=1e-6
    )


def test_projection_north_from_equator() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 0.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    expected_lat = math.degrees(1000.0 / _EARTH_RADIUS_M)
    assert math.isclose(
        result["target_latitude"].iloc[0], expected_lat, rel_tol=1e-6
    )
    assert math.isclose(result["target_longitude"].iloc[0], 0.0, abs_tol=1e-6)


def test_depth_reduces_horizontal_range() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 5.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [3.0, 3.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    assert math.isclose(result["horizontal_range"].iloc[0], 4.0, rel_tol=1e-9)


def test_depth_exceeds_slant_range_clamps_to_zero() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 3.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [5.0, 5.0]
    )

    result = resolve_usbl_position(usbl, pressure)

    assert result["horizontal_range"].iloc[0] == 0.0


def test_depth_interpolation() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"],
        [10.0, 20.0],
    )

    result = resolve_usbl_position(usbl, pressure)

    assert math.isclose(result["target_depth"].iloc[0], 15.0, abs_tol=0.1)


def test_relative_bearing_adds_ship_heading() -> None:
    usbl_abs = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 90.0, 135.0, 1000.0)]
    )
    usbl_rel = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 90.0, 45.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result_abs = resolve_usbl_position(
        usbl_abs,
        pressure,
        UsblResolvePositionConfig(bearing_reference="absolute"),
    )
    result_rel = resolve_usbl_position(
        usbl_rel,
        pressure,
        UsblResolvePositionConfig(bearing_reference="relative"),
    )

    assert math.isclose(
        result_abs["target_latitude"].iloc[0],
        result_rel["target_latitude"].iloc[0],
        rel_tol=1e-9,
    )
    assert math.isclose(
        result_abs["target_longitude"].iloc[0],
        result_rel["target_longitude"].iloc[0],
        rel_tol=1e-9,
    )


def test_usbl_before_pressure_window_raises() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:20:00", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = UsblResolvePositionConfig(max_time_gap_seconds=60.0)
    with pytest.raises(ValueError, match="precedes first pressure reading"):
        resolve_usbl_position(usbl, pressure, config)


def test_usbl_after_pressure_window_raises() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:25:00", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = UsblResolvePositionConfig(max_time_gap_seconds=60.0)
    with pytest.raises(ValueError, match="follows last pressure reading"):
        resolve_usbl_position(usbl, pressure, config)


def test_usbl_within_time_margin_does_not_raise() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:21:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = UsblResolvePositionConfig(max_time_gap_seconds=60.0)
    resolve_usbl_position(usbl, pressure, config)
