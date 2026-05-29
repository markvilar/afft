"""Tests for the pressure sensor uncertainty processor."""

import math

import pandas as pd

from afft.telemetry_processing.pressure_parosci import (
    PressureUncertaintyConfig,
    estimate_pressure_uncertainty,
)


def _make_df(depths: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"timestamp": "2010-04-21 02:27:56.000", "depth": depths}
    )


def test_output_column_present():
    result = estimate_pressure_uncertainty(_make_df([10.0]))
    assert "depth_uncertainty" in result.columns


def test_constant_uncertainty_default():
    result = estimate_pressure_uncertainty(_make_df([0.0, 50.0, 100.0]))
    assert (result["depth_uncertainty"] == 0.005).all()


def test_constant_uncertainty_configurable():
    config = PressureUncertaintyConfig(base_uncertainty=0.5)
    result = estimate_pressure_uncertainty(_make_df([10.0, 20.0]), config)
    assert (result["depth_uncertainty"] == 0.5).all()


def test_depth_proportional_term():
    config = PressureUncertaintyConfig(base_uncertainty=0.1, depth_scale=0.001)
    result = estimate_pressure_uncertainty(_make_df([100.0]), config)
    assert math.isclose(result["depth_uncertainty"].iloc[0], 0.2, rel_tol=1e-9)


def test_zero_depth_gives_base_uncertainty():
    config = PressureUncertaintyConfig(base_uncertainty=0.25, depth_scale=0.01)
    result = estimate_pressure_uncertainty(_make_df([0.0]), config)
    assert math.isclose(result["depth_uncertainty"].iloc[0], 0.25, rel_tol=1e-9)


def test_input_rows_preserved():
    df = _make_df([1.0, 2.0, 3.0])
    result = estimate_pressure_uncertainty(df)
    assert len(result) == len(df)
    assert list(result["depth"]) == list(df["depth"])
