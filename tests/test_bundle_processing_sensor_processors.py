"""Tests for the pipeline wrappers around the sensor processing functions,
covering what the wrappers add rather than the processors they call."""

import pandas as pd
import pytest

from afft.bundle_processing.sensor_processors import (
    step_process_evologics_usbl,
    step_process_tracklink_usbl_from_messages,
)
from afft.sensors.usbl_evologics import EvologicsProcessingConfig
from afft.sensors.usbl_linkquest import TrackLinkProcessingFromMessagesConfig


def _extrinsics_frame(rows: int = 1) -> pd.DataFrame:
    """A frame shaped as the bundle builder writes `SensorExtrinsics`."""
    return pd.DataFrame(
        {
            "locx": [1.0] * rows,
            "locy": [2.0] * rows,
            "locz": [3.0] * rows,
            "rotx": [0.0] * rows,
            "roty": [0.0] * rows,
            "rotz": [0.0] * rows,
        }
    )


def _evologics_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": ["2017-05-23 04:08:16+00:00"],
            "target_latitude": [-32.035152],
            "target_longitude": [115.459240],
            "target_depth": [12.0],
            "target_x": [1.0],
            "target_y": [2.0],
            "target_z": [-3.0],
            "ship_latitude": [-32.03],
            "ship_longitude": [115.46],
            "ship_heading": [10.0],
            "ship_roll": [0.0],
            "ship_pitch": [0.0],
            "accuracy": [1.5],
        }
    )


def _tracklink_frames() -> dict[str, pd.DataFrame]:
    usbl = pd.DataFrame(
        {
            "timestamp": ["2010-04-21 02:22:30"],
            "ship_latitude": [0.0],
            "ship_longitude": [0.0],
            "ship_heading": [0.0],
            "ship_roll": [0.0],
            "ship_pitch": [0.0],
            "target_bearing_angle": [90.0],
            "target_slant_range": [100.0],
        }
    )
    pressure = pd.DataFrame(
        {
            "timestamp": ["2010-04-21 02:22:29", "2010-04-21 02:22:31"],
            "depth": [5.0, 5.0],
        }
    )
    return {"usbl": usbl, "pressure": pressure}


def test_extrinsics_frame_is_applied_to_the_evologics_step() -> None:
    """The bundle's extrinsics frame reaches the processor."""
    frames = {
        "usbl": _evologics_frame(),
        "extrinsics": _extrinsics_frame(),
    }

    result = step_process_evologics_usbl(frames, EvologicsProcessingConfig())

    assert (result["usbl_extrinsics_locx"] == 1.0).all()
    assert (result["usbl_extrinsics_locy"] == 2.0).all()
    assert (result["usbl_extrinsics_locz"] == 3.0).all()
    assert result["usbl_extrinsics_applied"].all()


def test_omitting_the_extrinsics_input_disables_the_correction() -> None:
    """Absence of the input is the disable signal -- there is no flag."""
    frames = {"usbl": _evologics_frame()}

    result = step_process_evologics_usbl(frames, EvologicsProcessingConfig())

    assert not result["usbl_extrinsics_applied"].any()
    assert (result["usbl_extrinsics_locx"] == 0.0).all()


def test_extrinsics_frame_is_applied_to_the_tracklink_step() -> None:
    frames = _tracklink_frames() | {"extrinsics": _extrinsics_frame()}

    result = step_process_tracklink_usbl_from_messages(
        frames, TrackLinkProcessingFromMessagesConfig()
    )

    assert (result["usbl_extrinsics_locy"] == 2.0).all()
    assert result["usbl_extrinsics_applied"].all()


def test_a_multi_row_extrinsics_frame_is_rejected() -> None:
    """Taking the first row would shift every position by a plausible amount."""
    frames = {
        "usbl": _evologics_frame(),
        "extrinsics": _extrinsics_frame(rows=2),
    }

    with pytest.raises(ValueError, match="holds 2 rows"):
        step_process_evologics_usbl(frames, EvologicsProcessingConfig())


def test_an_empty_extrinsics_frame_is_rejected() -> None:
    frames = {
        "usbl": _evologics_frame(),
        "extrinsics": _extrinsics_frame(rows=0),
    }

    with pytest.raises(ValueError, match="holds 0 rows"):
        step_process_evologics_usbl(frames, EvologicsProcessingConfig())


def test_an_extrinsics_frame_with_unexpected_columns_is_rejected() -> None:
    """`extra="forbid"` is what catches a bundle written against a changed
    `SensorExtrinsics`, so the decode must not drop unknown columns."""
    frame = _extrinsics_frame()
    frame["unexpected"] = [0.0]
    frames = {"usbl": _evologics_frame(), "extrinsics": frame}

    with pytest.raises(ValueError, match="does not match"):
        step_process_evologics_usbl(frames, EvologicsProcessingConfig())


def test_an_extrinsics_frame_missing_a_field_is_rejected() -> None:
    frame = _extrinsics_frame().drop(columns=["rotz"])
    frames = {"usbl": _evologics_frame(), "extrinsics": frame}

    with pytest.raises(ValueError, match="does not match"):
        step_process_evologics_usbl(frames, EvologicsProcessingConfig())
