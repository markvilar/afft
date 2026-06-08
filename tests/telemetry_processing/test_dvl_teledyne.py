"""Tests for the DVL uncertainty processor."""

import pandas as pd

from afft.sensors.dvl_teledyne import (
    DvlUncertaintyConfig,
    estimate_dvl_uncertainty,
)

_VELOCITY_COLS = [
    "velocity_x_uncertainty",
    "velocity_y_uncertainty",
    "velocity_z_uncertainty",
]
_ATTITUDE_COLS = [
    "roll_uncertainty",
    "pitch_uncertainty",
    "heading_uncertainty",
]


def _make_df(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _row(
    vx: float = 1.0, vy: float = 0.0, vz: float = 0.0
) -> dict[str, object]:
    return {
        "timestamp": "2010-04-21 02:27:56.000",
        "velocity_x": vx,
        "velocity_y": vy,
        "velocity_z": vz,
        "altitude": 5.0,
        "heading": 180.0,
        "pitch": 0.0,
        "roll": 0.0,
        "bottom_track_status": 1,
    }


BASE_ROWS = [_row(1.0, 0.0, 0.0), _row(0.0, 2.0, 0.0), _row(0.0, 0.0, 3.0)]


def test_output_columns() -> None:
    result = estimate_dvl_uncertainty(_make_df(BASE_ROWS))
    for col in _VELOCITY_COLS + _ATTITUDE_COLS:
        assert col in result.columns


def test_velocity_uncertainties_are_constant() -> None:
    config = DvlUncertaintyConfig(
        velocity_x_uncertainty=0.003,
        velocity_y_uncertainty=0.003,
        velocity_z_uncertainty=0.003,
    )
    result = estimate_dvl_uncertainty(_make_df(BASE_ROWS), config)
    assert (result["velocity_x_uncertainty"] == 0.003).all()
    assert (result["velocity_y_uncertainty"] == 0.003).all()
    assert (result["velocity_z_uncertainty"] == 0.003).all()


def test_attitude_uncertainties_are_constant() -> None:
    config = DvlUncertaintyConfig(
        roll_uncertainty=0.25,
        pitch_uncertainty=0.25,
        heading_uncertainty=1.0,
    )
    result = estimate_dvl_uncertainty(_make_df(BASE_ROWS), config)
    assert (result["roll_uncertainty"] == 0.25).all()
    assert (result["pitch_uncertainty"] == 0.25).all()
    assert (result["heading_uncertainty"] == 1.0).all()


def test_per_axis_velocity_uncertainties_can_differ() -> None:
    config = DvlUncertaintyConfig(
        velocity_x_uncertainty=0.001,
        velocity_y_uncertainty=0.002,
        velocity_z_uncertainty=0.004,
    )
    result = estimate_dvl_uncertainty(_make_df([_row()]), config)
    assert result["velocity_x_uncertainty"].iloc[0] == 0.001
    assert result["velocity_y_uncertainty"].iloc[0] == 0.002
    assert result["velocity_z_uncertainty"].iloc[0] == 0.004


def test_roll_pitch_heading_can_differ() -> None:
    config = DvlUncertaintyConfig(
        roll_uncertainty=0.25,
        pitch_uncertainty=0.25,
        heading_uncertainty=2.0,
    )
    result = estimate_dvl_uncertainty(_make_df([_row()]), config)
    assert result["roll_uncertainty"].iloc[0] == 0.25
    assert result["pitch_uncertainty"].iloc[0] == 0.25
    assert result["heading_uncertainty"].iloc[0] == 2.0


def test_defaults_match_rdi_spec() -> None:
    result = estimate_dvl_uncertainty(_make_df([_row()]))
    assert result["velocity_x_uncertainty"].iloc[0] == 0.003
    assert result["velocity_y_uncertainty"].iloc[0] == 0.003
    assert result["velocity_z_uncertainty"].iloc[0] == 0.003
    assert result["roll_uncertainty"].iloc[0] == 0.25
    assert result["pitch_uncertainty"].iloc[0] == 0.25
    assert result["heading_uncertainty"].iloc[0] == 1.0


def test_input_rows_preserved() -> None:
    df = _make_df(BASE_ROWS)
    result = estimate_dvl_uncertainty(df)
    assert len(result) == len(df)
    assert list(result["velocity_x"]) == list(df["velocity_x"])
