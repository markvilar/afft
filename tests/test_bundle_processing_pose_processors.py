"""Tests for the generic pose-frame extrinsics processor."""

import geopandas as gpd
import pandas as pd
import pymap3d
import pytest
from shapely.geometry import Point

from afft.bundle_processing import default_registry
from afft.bundle_processing.pose_processors import (
    ApplyMountingOffsetConfig,
    apply_mounting_offset,
    step_apply_mounting_offset,
)
from afft.deployment import SensorExtrinsics

_ORIGIN_LATITUDE: float = -32.035152
_ORIGIN_LONGITUDE: float = 115.459240
_ORIGIN_HEIGHT: float = 10.0


def _pose_frame(heading: float = 0.0) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "heading": [heading],
            "pitch": [0.0],
            "roll": [0.0],
            "label": ["pose-0"],
        },
        geometry=[Point(_ORIGIN_LONGITUDE, _ORIGIN_LATITUDE, _ORIGIN_HEIGHT)],
        crs="EPSG:4326",
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
    source: gpd.GeoDataFrame, target: gpd.GeoDataFrame
) -> tuple[float, float]:
    """North and east displacement from `source` to `target`, in metres."""
    north: float
    east: float
    north, east, _ = pymap3d.geodetic2ned(
        target.geometry.y.iloc[0],
        target.geometry.x.iloc[0],
        0.0,
        source.geometry.y.iloc[0],
        source.geometry.x.iloc[0],
        0.0,
    )
    return float(north), float(east)


def test_apply_mounting_offset_shifts_horizontally() -> None:
    poses: gpd.GeoDataFrame = _pose_frame(heading=0.0)
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5)

    shifted: gpd.GeoDataFrame = apply_mounting_offset(
        poses, extrinsics, ApplyMountingOffsetConfig()
    )

    north, east = _displacement(poses, shifted)
    assert north == pytest.approx(-1.0, abs=1e-3)
    assert east == pytest.approx(-0.5, abs=1e-3)


def test_apply_mounting_offset_shifts_vertically() -> None:
    poses: gpd.GeoDataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locz=2.0)

    shifted: gpd.GeoDataFrame = apply_mounting_offset(
        poses, extrinsics, ApplyMountingOffsetConfig()
    )

    assert shifted.geometry.z.iloc[0] == pytest.approx(
        _ORIGIN_HEIGHT + 2.0, abs=1e-6
    )


def test_apply_mounting_offset_preserves_crs() -> None:
    poses: gpd.GeoDataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0)

    shifted: gpd.GeoDataFrame = apply_mounting_offset(
        poses, extrinsics, ApplyMountingOffsetConfig()
    )

    assert shifted.crs == poses.crs


def test_apply_mounting_offset_passes_other_columns_through() -> None:
    poses: gpd.GeoDataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0)

    shifted: gpd.GeoDataFrame = apply_mounting_offset(
        poses, extrinsics, ApplyMountingOffsetConfig()
    )

    assert shifted["label"].iloc[0] == "pose-0"


def test_apply_mounting_offset_invert_reverses_the_shift() -> None:
    poses: gpd.GeoDataFrame = _pose_frame()
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5, locz=2.0)

    forward: gpd.GeoDataFrame = apply_mounting_offset(
        poses, extrinsics, ApplyMountingOffsetConfig()
    )
    round_tripped: gpd.GeoDataFrame = apply_mounting_offset(
        forward, extrinsics, ApplyMountingOffsetConfig(invert=True)
    )

    assert round_tripped.geometry.y.iloc[0] == pytest.approx(
        poses.geometry.y.iloc[0], abs=1e-9
    )
    assert round_tripped.geometry.x.iloc[0] == pytest.approx(
        poses.geometry.x.iloc[0], abs=1e-9
    )
    assert round_tripped.geometry.z.iloc[0] == pytest.approx(
        poses.geometry.z.iloc[0], abs=1e-6
    )


def test_step_apply_mounting_offset_requires_extrinsics_input() -> None:
    frames = {"poses": _pose_frame()}

    with pytest.raises(KeyError):
        step_apply_mounting_offset(frames, ApplyMountingOffsetConfig())


def test_step_apply_mounting_offset_rejects_multi_row_extrinsics() -> None:
    extrinsics_frame: pd.DataFrame = pd.concat(
        [_extrinsics_frame(_extrinsics(locx=1.0))] * 2, ignore_index=True
    )
    frames = {"poses": _pose_frame(), "extrinsics": extrinsics_frame}

    with pytest.raises(ValueError, match="expected exactly 1"):
        step_apply_mounting_offset(frames, ApplyMountingOffsetConfig())


def test_step_apply_mounting_offset_matches_direct_call() -> None:
    extrinsics: SensorExtrinsics = _extrinsics(locx=1.0, locy=0.5, locz=2.0)
    frames = {
        "poses": _pose_frame(),
        "extrinsics": _extrinsics_frame(extrinsics),
    }

    from_step: gpd.GeoDataFrame = step_apply_mounting_offset(
        frames, ApplyMountingOffsetConfig()
    )
    direct: gpd.GeoDataFrame = apply_mounting_offset(
        frames["poses"], extrinsics, ApplyMountingOffsetConfig()
    )

    assert from_step.equals(direct)
    assert from_step.crs == direct.crs


def test_apply_mounting_offset_is_registered() -> None:
    registered = default_registry().get("apply_mounting_offset")
    assert registered.processor is step_apply_mounting_offset
    assert registered.config_type is ApplyMountingOffsetConfig
