"""Tests for the TrackLink USBL uncertainty processor."""

import pandas as pd

from afft.sensors.usbl_linkquest import (
    TrackLinkUncertaintyConfig,
    estimate_usbl_uncertainty,
)


def _make_df(rows: int = 2) -> pd.DataFrame:
    return pd.DataFrame({"timestamp": ["2010-04-21 02:22:30"] * rows})


def test_output_columns_present() -> None:
    result = estimate_usbl_uncertainty(_make_df())
    assert "horizontal_position_std" in result.columns
    assert "depth_position_std" in result.columns


def test_input_rows_preserved() -> None:
    result = estimate_usbl_uncertainty(_make_df(rows=5))
    assert len(result) == 5


def test_horizontal_position_std_value() -> None:
    config = TrackLinkUncertaintyConfig(
        horizontal_position_std=12.5, depth_position_std=3.0
    )
    result = estimate_usbl_uncertainty(_make_df(), config)
    assert (result["horizontal_position_std"] == 12.5).all()


def test_depth_position_std_value() -> None:
    config = TrackLinkUncertaintyConfig(
        horizontal_position_std=12.5, depth_position_std=3.0
    )
    result = estimate_usbl_uncertainty(_make_df(), config)
    assert (result["depth_position_std"] == 3.0).all()


def test_input_not_mutated() -> None:
    df = _make_df()
    estimate_usbl_uncertainty(df)
    assert "horizontal_position_std" not in df.columns
    assert "depth_position_std" not in df.columns
