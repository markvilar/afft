"""Tests for the Evologics USBL processor."""

import math

import pandas as pd

from afft.sensors.usbl_evologics import (
    EvologicsProcessingConfig,
    EvologicsTransceiverExtrinsics,
    process_evologics_usbl,
)


def _make_df(rows: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "topic": ["EVOLOGICS_FIX"] * rows,
            "timestamp": ["2017-05-23 04:08:16+00:00"] * rows,
            "target_latitude": [-32.035152] * rows,
            "target_longitude": [115.459240] * rows,
            "target_depth": [4.537] * rows,
            "target_x": [2.73] * rows,
            "target_y": [-53.8] * rows,
            "target_z": [0.19] * rows,
            "accuracy": [1.191] * rows,
            "ship_latitude": [-32.035473] * rows,
            "ship_longitude": [115.458771] * rows,
            "ship_roll": [-2.31] * rows,
            "ship_pitch": [-0.19] * rows,
            "ship_heading": [213.22] * rows,
        }
    )


def test_output_columns_present() -> None:
    result = process_evologics_usbl(_make_df())
    for col in [
        "target_x_sensor",
        "target_y_sensor",
        "target_z_sensor",
        "target_x_vessel",
        "target_y_vessel",
        "target_z_vessel",
        "target_horizontal_range",
        "target_inclination_angle",
        "horizontal_position_std",
        "depth_position_std",
        "evologics_accuracy",
        "usbl_extrinsics_x",
        "usbl_extrinsics_y",
        "usbl_extrinsics_z",
        "usbl_extrinsics_phi",
        "usbl_extrinsics_theta",
        "usbl_extrinsics_psi",
    ]:
        assert col in result.columns


def test_accuracy_renamed() -> None:
    result = process_evologics_usbl(_make_df())
    assert "evologics_accuracy" in result.columns
    assert "accuracy" not in result.columns


def test_accuracy_values_preserved() -> None:
    result = process_evologics_usbl(_make_df())
    assert (result["evologics_accuracy"] == 1.191).all()


def test_input_rows_preserved() -> None:
    result = process_evologics_usbl(_make_df(rows=5))
    assert len(result) == 5


def test_input_not_mutated() -> None:
    df = _make_df()
    process_evologics_usbl(df)
    assert "evologics_accuracy" not in df.columns
    assert "accuracy" in df.columns


def test_horizontal_range_from_vessel_frame() -> None:
    # With no extrinsics, only the frame flip applies.
    # USBL (x=3, y=4, z=0) → Vessel (x=4, y=3, z=0) → range=5
    df = _make_df(rows=1)
    df["target_x"] = 3.0
    df["target_y"] = 4.0
    df["target_z"] = 0.0
    result = process_evologics_usbl(df)
    assert math.isclose(
        result["target_horizontal_range"].iloc[0], 5.0, rel_tol=1e-9
    )


def test_frame_flip_no_extrinsics() -> None:
    # USBL (x=1, y=0, z=0) → flip → Vessel (x=0, y=1, z=0)
    df = _make_df(rows=1)
    df["target_x"] = 1.0
    df["target_y"] = 0.0
    df["target_z"] = 0.0
    result = process_evologics_usbl(df)
    assert math.isclose(result["target_x_vessel"].iloc[0], 0.0, abs_tol=1e-12)
    assert math.isclose(result["target_y_vessel"].iloc[0], 1.0, rel_tol=1e-9)
    assert math.isclose(result["target_z_vessel"].iloc[0], 0.0, abs_tol=1e-12)


def test_z_axis_flipped_no_extrinsics() -> None:
    # USBL Z positive up → Vessel Z positive down (negated)
    df = _make_df(rows=1)
    df["target_x"] = 0.0
    df["target_y"] = 0.0
    df["target_z"] = 1.0
    result = process_evologics_usbl(df)
    assert math.isclose(result["target_z_vessel"].iloc[0], -1.0, rel_tol=1e-9)


def test_inclination_angle_horizontal_target() -> None:
    # Target directly to the side (no vertical offset) → inclination = 0
    df = _make_df(rows=1)
    df["target_x"] = 10.0
    df["target_y"] = 0.0
    df["target_z"] = 0.0
    result = process_evologics_usbl(df)
    assert math.isclose(
        result["target_inclination_angle"].iloc[0], 0.0, abs_tol=1e-9
    )


def test_inclination_angle_below_transceiver() -> None:
    # Target directly below transceiver → inclination = 90 degrees
    df = _make_df(rows=1)
    df["target_x"] = 0.0
    df["target_y"] = 0.0
    df["target_z"] = -10.0  # USBL Z negative = below
    result = process_evologics_usbl(df)
    assert math.isclose(
        result["target_inclination_angle"].iloc[0], 90.0, rel_tol=1e-6
    )


def test_uncertainty_values() -> None:
    config = EvologicsProcessingConfig(
        horizontal_position_std=12.5,
        depth_position_std=3.0,
    )
    result = process_evologics_usbl(_make_df(), config)
    assert (result["horizontal_position_std"] == 12.5).all()
    assert (result["depth_position_std"] == 3.0).all()


def test_extrinsics_columns_written() -> None:
    extrinsics = EvologicsTransceiverExtrinsics(
        x=1.0, y=2.0, z=3.0, phi=0.1, theta=0.2, psi=0.3
    )
    config = EvologicsProcessingConfig(extrinsics=extrinsics)
    result = process_evologics_usbl(_make_df(), config)
    assert (result["usbl_extrinsics_x"] == 1.0).all()
    assert (result["usbl_extrinsics_y"] == 2.0).all()
    assert (result["usbl_extrinsics_z"] == 3.0).all()
    assert (result["usbl_extrinsics_phi"] == 0.1).all()
    assert (result["usbl_extrinsics_theta"] == 0.2).all()
    assert (result["usbl_extrinsics_psi"] == 0.3).all()


def test_extrinsics_columns_zero_when_none() -> None:
    result = process_evologics_usbl(_make_df())
    for col in [
        "usbl_extrinsics_x",
        "usbl_extrinsics_y",
        "usbl_extrinsics_z",
        "usbl_extrinsics_phi",
        "usbl_extrinsics_theta",
        "usbl_extrinsics_psi",
    ]:
        assert (result[col] == 0.0).all()


def test_sensor_frame_preserves_usbl_frame_input() -> None:
    # Sensor-frame columns must contain the raw USBL-Frame values, unchanged.
    df = _make_df(rows=1)
    df["target_x"] = 3.0
    df["target_y"] = -7.0
    df["target_z"] = 1.5
    result = process_evologics_usbl(df)
    assert math.isclose(result["target_x_sensor"].iloc[0], 3.0, rel_tol=1e-9)
    assert math.isclose(result["target_y_sensor"].iloc[0], -7.0, rel_tol=1e-9)
    assert math.isclose(result["target_z_sensor"].iloc[0], 1.5, rel_tol=1e-9)


def test_extrinsics_translation_applied() -> None:
    # With only translation (no rotation), vessel-frame target = flipped + translation.
    # USBL (x=0, y=1, z=0) → flip → (x=1, y=0, z=0) → + (2, 3, 4) → (3, 3, 4)
    extrinsics = EvologicsTransceiverExtrinsics(x=2.0, y=3.0, z=4.0)
    config = EvologicsProcessingConfig(extrinsics=extrinsics)
    df = _make_df(rows=1)
    df["target_x"] = 0.0
    df["target_y"] = 1.0
    df["target_z"] = 0.0
    result = process_evologics_usbl(df, config)
    assert math.isclose(result["target_x_vessel"].iloc[0], 3.0, rel_tol=1e-9)
    assert math.isclose(result["target_y_vessel"].iloc[0], 3.0, rel_tol=1e-9)
    assert math.isclose(result["target_z_vessel"].iloc[0], 4.0, rel_tol=1e-9)
