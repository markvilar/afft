"""Tests for the generic pose-frame extrinsics processor."""

import pandas as pd
import pymap3d
import pytest

from afft.bundle_processing import default_registry
from afft.bundle_processing.pose_processors import (
    ApplySensorExtrinsicsConfig,
    apply_sensor_extrinsics,
    step_apply_sensor_extrinsics,
)
from afft.deployment import SensorExtrinsics

_ORIGIN_LATITUDE: float = -32.035152
_ORIGIN_LONGITUDE: float = 115.459240
_ORIGIN_HEIGHT: float = 10.0


def _pose_frame(heading: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "latitude": [_ORIGIN_LATITUDE],
            "longitude": [_ORIGIN_LONGITUDE],
            "height": [_ORIGIN_HEIGHT],
            "heading": [heading],
            "pitch": [0.0],
            "roll": [0.0],
            "label": ["pose-0"],
        }
    )


def _extrinsics(
    locx: float = 0.0,
    locy: float = 0.0,
    locz: float = 0.0,
) -> SensorExtrinsics:
    return SensorExtrinsics(
        locx=locx, locy=locy, locz=locz, rotx=0.0, roty=0.0, rotz=0.0
    )


def _extrinsics_frame(extrinsics: SensorExtrinsics) -> pd.DataFrame:
    return pd.DataFrame([extrinsics.model_dump()])


def _displacement(
    source: pd.DataFrame, target: pd.DataFrame
) -> tuple[float, float]:
    """North and east displacement from `source` to `target`, in metres."""
    north: float
    east: float
    north, east, _ = pymap3d.geodetic2ned(
        target["latitude"].iloc[0],
        target["longitude"].iloc[0],
        0.0,
        source["latitude"].iloc[0],
        source["longitude"].iloc[0],
        0.0,
    )
    return float(north), float(east)


def test_apply_sensor_extrinsics_shifts_horizontally() -> None:
    poses: pd.DataFrame = _pose_frame(heading=0.0)
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5)

    shifted: pd.DataFrame = apply_sensor_extrinsics(
        poses, extrinsics, ApplySensorExtrinsicsConfig()
    )

    north, east = _displacement(poses, shifted)
    assert north == pytest.approx(-1.0, abs=1e-3)
    assert east == pytest.approx(-0.5, abs=1e-3)


def test_apply_sensor_extrinsics_shifts_vertically() -> None:
    poses: pd.DataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locz=2.0)

    shifted: pd.DataFrame = apply_sensor_extrinsics(
        poses, extrinsics, ApplySensorExtrinsicsConfig()
    )

    assert shifted["height"].iloc[0] == pytest.approx(
        _ORIGIN_HEIGHT + 2.0, abs=1e-6
    )


def test_apply_sensor_extrinsics_passes_other_columns_through() -> None:
    poses: pd.DataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0)

    shifted: pd.DataFrame = apply_sensor_extrinsics(
        poses, extrinsics, ApplySensorExtrinsicsConfig()
    )

    assert shifted["label"].iloc[0] == "pose-0"


def test_apply_sensor_extrinsics_invert_reverses_the_shift() -> None:
    poses: pd.DataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5, locz=2.0)

    forward: pd.DataFrame = apply_sensor_extrinsics(
        poses, extrinsics, ApplySensorExtrinsicsConfig()
    )
    round_tripped: pd.DataFrame = apply_sensor_extrinsics(
        forward, extrinsics, ApplySensorExtrinsicsConfig(invert=True)
    )

    assert round_tripped["latitude"].iloc[0] == pytest.approx(
        poses["latitude"].iloc[0], abs=1e-9
    )
    assert round_tripped["longitude"].iloc[0] == pytest.approx(
        poses["longitude"].iloc[0], abs=1e-9
    )
    assert round_tripped["height"].iloc[0] == pytest.approx(
        poses["height"].iloc[0], abs=1e-6
    )


def test_step_apply_sensor_extrinsics_requires_extrinsics_input() -> None:
    frames = {"poses": _pose_frame()}

    with pytest.raises(KeyError):
        step_apply_sensor_extrinsics(frames, ApplySensorExtrinsicsConfig())


def test_step_apply_sensor_extrinsics_rejects_multi_row_extrinsics() -> None:
    extrinsics_frame: pd.DataFrame = pd.concat(
        [_extrinsics_frame(_extrinsics(locx=1.0))] * 2, ignore_index=True
    )
    frames = {"poses": _pose_frame(), "extrinsics": extrinsics_frame}

    with pytest.raises(ValueError, match="expected exactly 1"):
        step_apply_sensor_extrinsics(frames, ApplySensorExtrinsicsConfig())


def test_step_apply_sensor_extrinsics_matches_direct_call() -> None:
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5, locz=2.0)
    frames = {
        "poses": _pose_frame(),
        "extrinsics": _extrinsics_frame(extrinsics),
    }

    from_step: pd.DataFrame = step_apply_sensor_extrinsics(
        frames, ApplySensorExtrinsicsConfig()
    )
    direct: pd.DataFrame = apply_sensor_extrinsics(
        frames["poses"], extrinsics, ApplySensorExtrinsicsConfig()
    )

    pd.testing.assert_frame_equal(from_step, direct)


def test_apply_sensor_extrinsics_is_registered() -> None:
    registered = default_registry().get("apply_sensor_extrinsics")
    assert registered.processor is step_apply_sensor_extrinsics
    assert registered.config_type is ApplySensorExtrinsicsConfig
