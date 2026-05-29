"""Tests for the stereo camera pair processor."""

import pandas as pd
import pytest

from afft.telemetry_processing.acfr_vision import (
    PairStereoImagesConfig,
    pair_stereo_images,
)


def _make_row(
    label: str,
    filename: str,
    trigger: float,
    timestamp: str,
    exposure_logged: bool = False,
    exposure: int = 0,
) -> dict:
    return {
        "topic": "VIS",
        "timestamp": timestamp,
        "label": label,
        "filename": filename,
        "trigger_time": trigger,
        "exposure_logged": exposure_logged,
        "exposure": exposure,
    }


BASE_ROWS = [
    # trigger 1.0 — LC16 has duplicate rows, RM16 has one
    _make_row("PR_001_RM16", "PR_001_RM16.pgm", 1.0, "2010-04-21 02:27:56.341"),
    _make_row("PR_001_LC16", "PR_001_LC16.pgm", 1.0, "2010-04-21 02:27:56.345"),
    _make_row("PR_001_LC16", "PR_001_LC16.pgm", 1.0, "2010-04-21 02:27:56.355"),
    _make_row("PR_001_LC16", "PR_001_LC16.pgm", 1.0, "2010-04-21 02:27:56.365"),
    # trigger 2.0 — clean pair
    _make_row("PR_002_RM16", "PR_002_RM16.pgm", 2.0, "2010-04-21 02:27:57.391"),
    _make_row("PR_002_LC16", "PR_002_LC16.pgm", 2.0, "2010-04-21 02:27:57.400"),
]


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_basic_pairing():
    result = pair_stereo_images(_df(BASE_ROWS))

    assert len(result) == 2
    assert set(result.columns) == {
        "timestamp",
        "left_label",
        "right_label",
        "left_filename",
        "right_filename",
        "left_timestamp",
        "right_timestamp",
        "left_received_at",
        "right_received_at",
        "left_exposure_logged",
        "left_exposure",
        "right_exposure_logged",
        "right_exposure",
    }


def test_deduplication():
    result = pair_stereo_images(_df(BASE_ROWS))
    assert len(result[result["left_timestamp"] == 1.0]) == 1


def test_left_right_assignment():
    result = pair_stereo_images(_df(BASE_ROWS))
    assert result["left_filename"].str.contains("LC16").all()
    assert result["right_filename"].str.contains("RM16").all()


def test_custom_suffixes():
    rows = [
        _make_row(
            "img_LEFT_01", "img_LEFT_01.pgm", 1.0, "2010-04-21 02:27:56.341"
        ),
        _make_row(
            "img_RIGHT_01", "img_RIGHT_01.pgm", 1.0, "2010-04-21 02:27:56.345"
        ),
    ]
    config = PairStereoImagesConfig(left_suffix="LEFT", right_suffix="RIGHT")
    result = pair_stereo_images(_df(rows), config)
    assert len(result) == 1


def test_no_left_raises():
    rows = [
        _make_row(
            "PR_001_RM16", "PR_001_RM16.pgm", 1.0, "2010-04-21 02:27:56.341"
        )
    ]
    with pytest.raises(ValueError, match="left_suffix"):
        pair_stereo_images(_df(rows))


def test_no_right_raises():
    rows = [
        _make_row(
            "PR_001_LC16", "PR_001_LC16.pgm", 1.0, "2010-04-21 02:27:56.341"
        )
    ]
    with pytest.raises(ValueError, match="right_suffix"):
        pair_stereo_images(_df(rows))


def test_trigger_time_offset_validation():
    # Trigger times differ by 100 ms — exceeds the 30 ms tolerance.
    rows = [
        _make_row(
            "PR_001_RM16", "PR_001_RM16.pgm", 1.000, "2010-04-21 02:27:56.000"
        ),
        _make_row(
            "PR_001_LC16", "PR_001_LC16.pgm", 1.100, "2010-04-21 02:27:56.100"
        ),
    ]
    config = PairStereoImagesConfig(max_offset_ms=30.0)
    with pytest.raises(ValueError, match="no stereo pairs remain"):
        pair_stereo_images(_df(rows), config)
