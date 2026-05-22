"""Tests for the USBL uncertainty processor."""

import math

import numpy as np
import pandas as pd
import pytest

from afft.telemetry.usbl import UsblUncertaintyConfig, estimate_usbl_uncertainty


def _make_df(slant_range: list[float], horizontal_range: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": "2010-04-21 02:22:30",
            "range": slant_range,
            "horizontal_range": horizontal_range,
        }
    )


def test_output_column_present():
    result = estimate_usbl_uncertainty(_make_df([10.0], [8.0]))
    assert "position_uncertainty" in result.columns


def test_input_rows_preserved():
    df = _make_df([10.0, 20.0], [8.0, 16.0])
    result = estimate_usbl_uncertainty(df)
    assert len(result) == len(df)


def test_range_term_only_when_bearing_uncertainty_zero():
    config = UsblUncertaintyConfig(range_uncertainty=1.0, bearing_uncertainty=0.0)
    result = estimate_usbl_uncertainty(_make_df([10.0], [8.0]), config)
    expected = 1.0 * 10.0 / 8.0
    assert math.isclose(result["position_uncertainty"].iloc[0], expected, rel_tol=1e-9)


def test_bearing_term_only_when_range_uncertainty_zero():
    config = UsblUncertaintyConfig(range_uncertainty=0.0, bearing_uncertainty=1.0)
    result = estimate_usbl_uncertainty(_make_df([10.0], [8.0]), config)
    expected = 8.0 * math.radians(1.0)
    assert math.isclose(result["position_uncertainty"].iloc[0], expected, rel_tol=1e-9)


def test_combined_uncertainty_in_quadrature():
    R, h = 5.0, 3.0
    sigma_r, sigma_theta_deg = 0.5, 0.5
    expected = math.sqrt(
        (sigma_r * R / h) ** 2 + (h * math.radians(sigma_theta_deg)) ** 2
    )
    config = UsblUncertaintyConfig(range_uncertainty=sigma_r, bearing_uncertainty=sigma_theta_deg)
    result = estimate_usbl_uncertainty(_make_df([R], [h]), config)
    assert math.isclose(result["position_uncertainty"].iloc[0], expected, rel_tol=1e-9)


def test_uncertainty_increases_with_slant_range():
    df = _make_df([10.0, 50.0, 100.0], [10.0, 50.0, 100.0])
    result = estimate_usbl_uncertainty(df)
    uncertainty = result["position_uncertainty"].to_numpy()
    assert (np.diff(uncertainty) > 0).all()


def test_zero_horizontal_range_does_not_raise():
    result = estimate_usbl_uncertainty(_make_df([5.0], [0.0]))
    assert np.isfinite(result["position_uncertainty"].iloc[0])


def test_missing_horizontal_range_raises():
    df = pd.DataFrame({"timestamp": ["2010-04-21 02:22:30"], "range": [10.0]})
    with pytest.raises(KeyError, match="horizontal_range"):
        estimate_usbl_uncertainty(df)
