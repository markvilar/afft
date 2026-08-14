"""Tests for the pressure sensor processors."""

import math

import pandas as pd
import pytest

from afft.sensors.pressure_parosci import (
    PressureUncertaintyConfig,
    SeaLevelCorrectionConfig,
    correct_pressure_for_sea_level,
    estimate_pressure_uncertainty,
)
from afft.utils.log import logger


def _make_df(depths: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"timestamp": "2010-04-21 02:27:56.000", "depth": depths}
    )


def _pressure_frame(timestamps: list[str], depths: list[float]) -> pd.DataFrame:
    """A pressure frame typed as the bundle stores it."""
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, utc=True),
            "depth": depths,
        }
    )


def _sea_level_frame(
    timestamps: list[str], levels: list[float]
) -> pd.DataFrame:
    """A tide frame typed as the WorldTides ingestion stores it."""
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, utc=True),
            "sea_level": levels,
        }
    )


def test_output_column_present() -> None:
    result = estimate_pressure_uncertainty(_make_df([10.0]))
    assert "depth_uncertainty" in result.columns


def test_constant_uncertainty_default() -> None:
    result = estimate_pressure_uncertainty(_make_df([0.0, 50.0, 100.0]))
    assert (result["depth_uncertainty"] == 0.005).all()


def test_constant_uncertainty_configurable() -> None:
    config = PressureUncertaintyConfig(base_uncertainty=0.5)
    result = estimate_pressure_uncertainty(_make_df([10.0, 20.0]), config)
    assert (result["depth_uncertainty"] == 0.5).all()


def test_depth_proportional_term() -> None:
    config = PressureUncertaintyConfig(base_uncertainty=0.1, depth_scale=0.001)
    result = estimate_pressure_uncertainty(_make_df([100.0]), config)
    assert math.isclose(result["depth_uncertainty"].iloc[0], 0.2, rel_tol=1e-9)


def test_zero_depth_gives_base_uncertainty() -> None:
    config = PressureUncertaintyConfig(base_uncertainty=0.25, depth_scale=0.01)
    result = estimate_pressure_uncertainty(_make_df([0.0]), config)
    assert math.isclose(result["depth_uncertainty"].iloc[0], 0.25, rel_tol=1e-9)


def test_input_rows_preserved() -> None:
    df = _make_df([1.0, 2.0, 3.0])
    result = estimate_pressure_uncertainty(df)
    assert len(result) == len(df)
    assert list(result["depth"]) == list(df["depth"])


def test_sea_level_columns_added() -> None:
    result = correct_pressure_for_sea_level(
        _pressure_frame(["2010-04-28T00:00:00Z"], [10.0]),
        _sea_level_frame(["2010-04-28T00:00:00Z"], [0.5]),
    )
    assert "sea_level" in result.columns
    assert "corrected_depth" in result.columns


def test_sea_level_subtracted_from_depth() -> None:
    result = correct_pressure_for_sea_level(
        _pressure_frame(["2010-04-28T00:00:00Z"], [10.0]),
        _sea_level_frame(["2010-04-28T00:00:00Z"], [0.5]),
    )
    assert math.isclose(result["corrected_depth"].iloc[0], 9.5, rel_tol=1e-9)


def test_sea_level_interpolated_between_samples() -> None:
    """A reading halfway between two hourly samples takes their midpoint."""
    result = correct_pressure_for_sea_level(
        _pressure_frame(["2010-04-28T00:30:00Z"], [10.0]),
        _sea_level_frame(
            ["2010-04-28T00:00:00Z", "2010-04-28T01:00:00Z"], [0.0, 1.0]
        ),
    )
    assert math.isclose(result["sea_level"].iloc[0], 0.5, rel_tol=1e-9)


def test_sea_level_clamped_outside_coverage() -> None:
    """Outside the tide series the endpoint value is held, not extrapolated."""
    result = correct_pressure_for_sea_level(
        _pressure_frame(["2010-04-28T05:00:00Z"], [10.0]),
        _sea_level_frame(
            ["2010-04-28T00:00:00Z", "2010-04-28T01:00:00Z"], [0.0, 1.0]
        ),
    )
    assert math.isclose(result["sea_level"].iloc[0], 1.0, rel_tol=1e-9)


def _capture_warnings(pressure: pd.DataFrame, sea_level: pd.DataFrame) -> str:
    """Run the correction, returning whatever it logged at WARNING."""
    messages: list[str] = []
    handler_id: int = logger.add(messages.append, level="WARNING")
    try:
        correct_pressure_for_sea_level(pressure, sea_level)
    finally:
        logger.remove(handler_id)
    return "".join(messages)


def test_coverage_gap_warns() -> None:
    logged = _capture_warnings(
        _pressure_frame(
            ["2010-04-28T00:00:00Z", "2010-04-28T09:00:00Z"], [10.0, 11.0]
        ),
        _sea_level_frame(["2010-04-28T00:00:00Z"], [0.5]),
    )
    assert "1 of 2 pressure readings" in logged
    assert "largest gap 32400 s" in logged
    assert "clamped" in logged


def test_coverage_within_threshold_does_not_warn() -> None:
    logged = _capture_warnings(
        _pressure_frame(["2010-04-28T00:30:00Z"], [10.0]),
        _sea_level_frame(
            ["2010-04-28T00:00:00Z", "2010-04-28T01:00:00Z"], [0.0, 1.0]
        ),
    )
    assert logged == ""


def test_empty_sea_level_frame_rejected() -> None:
    with pytest.raises(ValueError, match="no rows"):
        correct_pressure_for_sea_level(
            _pressure_frame(["2010-04-28T00:00:00Z"], [10.0]),
            _sea_level_frame([], []),
        )


def test_column_names_configurable() -> None:
    pressure = pd.DataFrame(
        {
            "time": pd.to_datetime(["2010-04-28T00:00:00Z"], utc=True),
            "d": [10.0],
        }
    )
    sea_level = pd.DataFrame(
        {
            "when": pd.to_datetime(["2010-04-28T00:00:00Z"], utc=True),
            "level": [0.5],
        }
    )
    config = SeaLevelCorrectionConfig(
        depth_col="d",
        timestamp_col="time",
        sea_level_col="level",
        sea_level_timestamp_col="when",
    )
    result = correct_pressure_for_sea_level(pressure, sea_level, config)
    assert math.isclose(result["corrected_depth"].iloc[0], 9.5, rel_tol=1e-9)


def test_input_frame_not_mutated() -> None:
    pressure = _pressure_frame(["2010-04-28T00:00:00Z"], [10.0])
    correct_pressure_for_sea_level(
        pressure, _sea_level_frame(["2010-04-28T00:00:00Z"], [0.5])
    )
    assert "corrected_depth" not in pressure.columns
