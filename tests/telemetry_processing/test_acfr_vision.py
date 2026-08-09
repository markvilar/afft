"""Tests for the stereo camera pair processor."""

import pandas as pd
import pytest

from afft.sensors.acfr_vision import (
    StereoPairingConfig,
    pair_stereo_images,
)


TRIGGER_1 = "2010-04-21 02:27:56.300+00:00"
TRIGGER_2 = "2010-04-21 02:27:57.350+00:00"


def _make_row(
    label: str,
    filename: str,
    trigger: str,
    timestamp: str,
    exposure_logged: bool = False,
    exposure: int = 0,
) -> dict[str, object]:
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
    # first trigger — LC16 has duplicate rows, RM16 has one
    _make_row(
        "PR_001_RM16", "PR_001_RM16.pgm", TRIGGER_1, "2010-04-21 02:27:56.341"
    ),
    _make_row(
        "PR_001_LC16", "PR_001_LC16.pgm", TRIGGER_1, "2010-04-21 02:27:56.345"
    ),
    _make_row(
        "PR_001_LC16", "PR_001_LC16.pgm", TRIGGER_1, "2010-04-21 02:27:56.355"
    ),
    _make_row(
        "PR_001_LC16", "PR_001_LC16.pgm", TRIGGER_1, "2010-04-21 02:27:56.365"
    ),
    # second trigger — clean pair
    _make_row(
        "PR_002_RM16", "PR_002_RM16.pgm", TRIGGER_2, "2010-04-21 02:27:57.391"
    ),
    _make_row(
        "PR_002_LC16", "PR_002_LC16.pgm", TRIGGER_2, "2010-04-21 02:27:57.400"
    ),
]


def _df(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a frame with the datetime64 trigger column bundles store."""
    df = pd.DataFrame(rows)
    df["trigger_time"] = pd.to_datetime(df["trigger_time"], utc=True)
    return df


def test_basic_pairing() -> None:
    result = pair_stereo_images(_df(BASE_ROWS))

    assert len(result.frame) == 2
    assert set(result.frame.columns) == {
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


def test_deduplication() -> None:
    result = pair_stereo_images(_df(BASE_ROWS))
    frame = result.frame
    assert len(frame[frame["left_timestamp"] == pd.Timestamp(TRIGGER_1)]) == 1


def test_left_right_assignment() -> None:
    result = pair_stereo_images(_df(BASE_ROWS))
    assert result.frame["left_filename"].str.contains("LC16").all()
    assert result.frame["right_filename"].str.contains("RM16").all()


def test_custom_suffixes() -> None:
    rows = [
        _make_row(
            "img_LEFT_01",
            "img_LEFT_01.pgm",
            TRIGGER_1,
            "2010-04-21 02:27:56.341",
        ),
        _make_row(
            "img_RIGHT_01",
            "img_RIGHT_01.pgm",
            TRIGGER_1,
            "2010-04-21 02:27:56.345",
        ),
    ]
    config = StereoPairingConfig(left_suffix="LEFT", right_suffix="RIGHT")
    result = pair_stereo_images(_df(rows), config)
    assert len(result.frame) == 1


def test_no_left_raises() -> None:
    rows = [
        _make_row(
            "PR_001_RM16",
            "PR_001_RM16.pgm",
            TRIGGER_1,
            "2010-04-21 02:27:56.341",
        )
    ]
    with pytest.raises(ValueError, match="left_suffix"):
        pair_stereo_images(_df(rows))


def test_no_right_raises() -> None:
    rows = [
        _make_row(
            "PR_001_LC16",
            "PR_001_LC16.pgm",
            TRIGGER_1,
            "2010-04-21 02:27:56.341",
        )
    ]
    with pytest.raises(ValueError, match="right_suffix"):
        pair_stereo_images(_df(rows))


def test_unmatched_left_preserves_right_dtypes() -> None:
    # The unpaired LC16 row forces a fill NaN into the right columns during
    # the merge. Once it is dropped, they must be bool/int again, not
    # object/float, or the frame cannot be serialised to HDF5.
    rows = BASE_ROWS + [
        _make_row(
            "PR_003_LC16",
            "PR_003_LC16.pgm",
            "2010-04-21 02:28:30.000+00:00",
            "2010-04-21 02:28:30.010",
        ),
    ]
    result = pair_stereo_images(_df(rows))

    assert result.frame["right_exposure_logged"].dtype == bool
    assert result.frame["right_exposure"].dtype == "int64"


def test_unmatched_right_is_dropped_and_counted() -> None:
    # The extra RM16 row pairs with nothing, so it must not reach the output
    # and must be counted the same way an unmatched left image is.
    rows = BASE_ROWS + [
        _make_row(
            "PR_003_RM16",
            "PR_003_RM16.pgm",
            "2010-04-21 02:28:30.000+00:00",
            "2010-04-21 02:28:30.010",
        ),
    ]
    result = pair_stereo_images(_df(rows))

    assert "PR_003_RM16" not in set(result.frame["right_label"])
    assert len(result.frame) == 2
    assert result.right_unmatched == 1
    assert result.right_total == 3
    assert result.left_unmatched == 0


def test_unmatched_left_is_counted() -> None:
    rows = BASE_ROWS + [
        _make_row(
            "PR_003_LC16",
            "PR_003_LC16.pgm",
            "2010-04-21 02:28:30.000+00:00",
            "2010-04-21 02:28:30.010",
        ),
    ]
    result = pair_stereo_images(_df(rows))

    assert result.left_unmatched == 1
    assert result.left_total == 3
    assert result.right_unmatched == 0


def test_fully_paired_reports_no_discards() -> None:
    result = pair_stereo_images(_df(BASE_ROWS))

    assert result.left_unmatched == 0
    assert result.right_unmatched == 0
    assert result.left_total == 2
    assert result.right_total == 2


def test_trigger_time_offset_validation() -> None:
    # Trigger times differ by 100 ms — exceeds the 30 ms tolerance.
    rows = [
        _make_row(
            "PR_001_RM16",
            "PR_001_RM16.pgm",
            "2010-04-21 02:27:56.000+00:00",
            "2010-04-21 02:27:56.000",
        ),
        _make_row(
            "PR_001_LC16",
            "PR_001_LC16.pgm",
            "2010-04-21 02:27:56.100+00:00",
            "2010-04-21 02:27:56.100",
        ),
    ]
    config = StereoPairingConfig(max_offset_ms=30.0)
    with pytest.raises(ValueError, match="no stereo pairs remain"):
        pair_stereo_images(_df(rows), config)
