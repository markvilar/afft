"""Tests for the USBL position resolution processor."""

import math

import pandas as pd
import pytest

from afft.sensors.usbl_linkquest import (
    TrackLinkResolvePositionFromMessagesConfig,
    TrackLinkTransceiverExtrinsics,
    resolve_target_position_from_messages,
)

# WGS84 ellipsoid parameters used by pymap3d
_WGS84_A_M: float = 6_378_137.0
_WGS84_E2: float = 0.006_694_379_990_14
# Radius of curvature at the equator in the meridional (north) direction
_WGS84_M_EQUATOR_M: float = _WGS84_A_M * (1.0 - _WGS84_E2)


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
        "target_bearing_angle": bearing,
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

    result = resolve_target_position_from_messages(usbl, pressure)

    for col in (
        "target_depth",
        "target_x_sensor",
        "target_y_sensor",
        "target_z_sensor",
        "target_x_vessel",
        "target_y_vessel",
        "target_z_vessel",
        "target_horizontal_range",
        "target_latitude",
        "target_longitude",
        "usbl_extrinsics_locx",
        "usbl_extrinsics_locy",
        "usbl_extrinsics_locz",
        "usbl_extrinsics_rotx",
        "usbl_extrinsics_roty",
        "usbl_extrinsics_rotz",
    ):
        assert col in result.columns


def test_zero_depth_horizontal_range_equals_slant_range() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_target_position_from_messages(usbl, pressure)

    assert math.isclose(
        result["target_horizontal_range"].iloc[0], 1000.0, rel_tol=1e-9
    )


def test_projection_east_from_equator() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_target_position_from_messages(usbl, pressure)

    expected_lon = math.degrees(1000.0 / _WGS84_A_M)
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

    result = resolve_target_position_from_messages(usbl, pressure)

    expected_lat = math.degrees(1000.0 / _WGS84_M_EQUATOR_M)
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

    result = resolve_target_position_from_messages(usbl, pressure)

    assert math.isclose(
        result["target_horizontal_range"].iloc[0], 4.0, rel_tol=1e-9
    )


def test_depth_exceeds_slant_range_clamps_to_zero() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 3.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [5.0, 5.0]
    )

    result = resolve_target_position_from_messages(usbl, pressure)

    assert result["target_horizontal_range"].iloc[0] == 0.0


def test_depth_interpolation() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"],
        [10.0, 20.0],
    )

    result = resolve_target_position_from_messages(usbl, pressure)

    assert math.isclose(result["target_depth"].iloc[0], 15.0, abs_tol=0.1)


def test_bearing_and_heading_compose() -> None:
    """Ship-body bearing and heading compose to the same compass direction."""
    # bearing=45° in ship body + heading=90° → compass 135°
    # bearing=135° in ship body + heading=0° → compass 135°
    usbl_a = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 90.0, 45.0, 1000.0)]
    )
    usbl_b = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 135.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result_a = resolve_target_position_from_messages(usbl_a, pressure)
    result_b = resolve_target_position_from_messages(usbl_b, pressure)

    assert math.isclose(
        result_a["target_latitude"].iloc[0],
        result_b["target_latitude"].iloc[0],
        rel_tol=1e-9,
    )
    assert math.isclose(
        result_a["target_longitude"].iloc[0],
        result_b["target_longitude"].iloc[0],
        rel_tol=1e-9,
    )


def test_usbl_before_pressure_window_raises() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:20:00", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = TrackLinkResolvePositionFromMessagesConfig(
        max_time_gap_seconds=60.0
    )
    with pytest.raises(ValueError, match="precedes first pressure reading"):
        resolve_target_position_from_messages(usbl, pressure, config)


def test_usbl_after_pressure_window_raises() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:25:00", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = TrackLinkResolvePositionFromMessagesConfig(
        max_time_gap_seconds=60.0
    )
    with pytest.raises(ValueError, match="follows last pressure reading"):
        resolve_target_position_from_messages(usbl, pressure, config)


def test_usbl_within_time_margin_does_not_raise() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:21:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:00", "2010-04-21 02:23:00"], [10.0, 10.0]
    )
    config = TrackLinkResolvePositionFromMessagesConfig(
        max_time_gap_seconds=60.0
    )
    resolve_target_position_from_messages(usbl, pressure, config)


# ---------------------------------------------------------------------------
# Extrinsics tests
# ---------------------------------------------------------------------------


def test_extrinsics_columns_written() -> None:
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 100.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [5.0, 5.0]
    )
    config = TrackLinkResolvePositionFromMessagesConfig(
        extrinsics=TrackLinkTransceiverExtrinsics(
            locx=1.0, locy=2.0, locz=3.0, rotx=0.1, roty=0.2, rotz=0.3
        )
    )
    result = resolve_target_position_from_messages(usbl, pressure, config)
    assert (result["usbl_extrinsics_locx"] == 1.0).all()
    assert (result["usbl_extrinsics_locy"] == 2.0).all()
    assert (result["usbl_extrinsics_locz"] == 3.0).all()
    assert (result["usbl_extrinsics_rotx"] == 0.1).all()
    assert (result["usbl_extrinsics_roty"] == 0.2).all()
    assert (result["usbl_extrinsics_rotz"] == 0.3).all()


def test_sensor_frame_columns_present_and_unrotated() -> None:
    """Sensor-frame XYZ is the raw transceiver-body value before extrinsics."""
    # bearing=90° (starboard in transceiver frame), zero depth → x=0, y=range
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )
    result = resolve_target_position_from_messages(usbl, pressure)

    assert math.isclose(result["target_x_sensor"].iloc[0], 0.0, abs_tol=1e-9)
    assert math.isclose(result["target_y_sensor"].iloc[0], 1000.0, rel_tol=1e-9)
    assert math.isclose(result["target_z_sensor"].iloc[0], 0.0, abs_tol=1e-9)


def test_extrinsics_yaw_rotates_bearing() -> None:
    """90° transceiver yaw: bearing 0° in transceiver frame → East compass."""
    # Default config (zero extrinsics): bearing 90° in ship body → East.
    usbl_ref = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 90.0, 1000.0)]
    )
    # 90° yaw extrinsics: transceiver points East; bearing 0° in transceiver
    # frame should also resolve to East in the world frame.
    usbl_ext = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 0.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result_ref = resolve_target_position_from_messages(usbl_ref, pressure)
    result_ext = resolve_target_position_from_messages(
        usbl_ext,
        pressure,
        TrackLinkResolvePositionFromMessagesConfig(
            extrinsics=TrackLinkTransceiverExtrinsics(
                locx=0.0, locy=0.0, locz=0.0, rotz=math.radians(90.0)
            )
        ),
    )

    assert math.isclose(
        result_ref["target_latitude"].iloc[0],
        result_ext["target_latitude"].iloc[0],
        abs_tol=1e-6,
    )
    assert math.isclose(
        result_ref["target_longitude"].iloc[0],
        result_ext["target_longitude"].iloc[0],
        rel_tol=1e-6,
    )


def test_extrinsics_translation_shifts_origin() -> None:
    """100 m starboard translation: transceiver is 100 m East of GPS (N-heading)."""
    # Ship heading North, level. Target at bearing 0° (North) at 500 m.
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 0.0, 0.0, 500.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    # Default (zero extrinsics): origin at GPS, target 500 m North.
    result_ref = resolve_target_position_from_messages(usbl, pressure)
    # 100 m starboard translation: transceiver is 100 m East of GPS.
    result_ext = resolve_target_position_from_messages(
        usbl,
        pressure,
        TrackLinkResolvePositionFromMessagesConfig(
            extrinsics=TrackLinkTransceiverExtrinsics(
                locx=0.0, locy=100.0, locz=0.0
            )
        ),
    )

    # Target longitude should be ~100 m East of the reference result.
    expected_lon_offset = math.degrees(100.0 / _WGS84_A_M)
    assert math.isclose(
        result_ext["target_longitude"].iloc[0],
        result_ref["target_longitude"].iloc[0] + expected_lon_offset,
        rel_tol=1e-4,
    )
    assert math.isclose(
        result_ext["target_latitude"].iloc[0],
        result_ref["target_latitude"].iloc[0],
        rel_tol=1e-6,
    )


def test_extrinsics_ship_heading_applied() -> None:
    """Heading 90° (East) + zero extrinsics: forward bearing resolves East."""
    usbl = _usbl_df(
        [_usbl_row("2010-04-21 02:22:30", 0.0, 0.0, 90.0, 0.0, 1000.0)]
    )
    pressure = _pressure_df(
        ["2010-04-21 02:22:29", "2010-04-21 02:22:31"], [0.0, 0.0]
    )

    result = resolve_target_position_from_messages(
        usbl,
        pressure,
        TrackLinkResolvePositionFromMessagesConfig(
            extrinsics=TrackLinkTransceiverExtrinsics(
                locx=0.0, locy=0.0, locz=0.0
            )
        ),
    )

    # Target 1000 m ahead of an East-heading ship → 1000 m East of GPS.
    expected_lon = math.degrees(1000.0 / _WGS84_A_M)
    assert math.isclose(result["target_latitude"].iloc[0], 0.0, abs_tol=1e-6)
    assert math.isclose(
        result["target_longitude"].iloc[0], expected_lon, rel_tol=1e-6
    )
