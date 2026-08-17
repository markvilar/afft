"""Tests for the generic geoframe-from-columns processor."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from afft.bundle_processing import default_registry
from afft.bundle_processing.geoframe_processors import (
    BuildGeoframeFromFrameConfig,
    build_geoframe_from_frame,
    step_build_geoframe_from_frame,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "longitude": [115.4, 115.5, 115.6],
            "latitude": [-32.0, -32.1, -32.2],
            "height": [10.0, 11.0, 12.0],
            "label": ["a", "b", "c"],
        }
    )


def test_build_geoframe_from_frame_builds_2d_points() -> None:
    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        _frame(),
        BuildGeoframeFromFrameConfig(
            x_column="longitude", y_column="latitude", crs="EPSG:4326"
        ),
    )

    assert result.geometry.iloc[0].x == pytest.approx(115.4)
    assert result.geometry.iloc[0].y == pytest.approx(-32.0)
    assert not result.geometry.iloc[0].has_z


def test_build_geoframe_from_frame_builds_3d_points() -> None:
    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        _frame(),
        BuildGeoframeFromFrameConfig(
            x_column="longitude",
            y_column="latitude",
            z_column="height",
            crs="EPSG:4326",
        ),
    )

    assert result.geometry.iloc[0].has_z
    assert result.geometry.iloc[0].z == pytest.approx(10.0)


def test_build_geoframe_from_frame_sets_crs() -> None:
    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        _frame(),
        BuildGeoframeFromFrameConfig(
            x_column="longitude", y_column="latitude", crs="EPSG:4326"
        ),
    )

    assert result.crs == "EPSG:4326"


def test_build_geoframe_from_frame_retains_source_columns() -> None:
    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        _frame(),
        BuildGeoframeFromFrameConfig(
            x_column="longitude", y_column="latitude", crs="EPSG:4326"
        ),
    )

    assert result["longitude"].tolist() == _frame()["longitude"].tolist()
    assert result["label"].tolist() == ["a", "b", "c"]


def test_build_geoframe_from_frame_drops_nan_xy_rows() -> None:
    frame: pd.DataFrame = _frame()
    frame.loc[1, "latitude"] = np.nan

    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        frame,
        BuildGeoframeFromFrameConfig(
            x_column="longitude", y_column="latitude", crs="EPSG:4326"
        ),
    )

    assert result["label"].tolist() == ["a", "c"]


def test_build_geoframe_from_frame_drops_nan_z_rows_when_z_configured() -> None:
    frame: pd.DataFrame = _frame()
    frame.loc[2, "height"] = np.nan

    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        frame,
        BuildGeoframeFromFrameConfig(
            x_column="longitude",
            y_column="latitude",
            z_column="height",
            crs="EPSG:4326",
        ),
    )

    assert result["label"].tolist() == ["a", "b"]


def test_build_geoframe_from_frame_ignores_nan_z_when_z_not_configured() -> (
    None
):
    frame: pd.DataFrame = _frame()
    frame.loc[2, "height"] = np.nan

    result: gpd.GeoDataFrame = build_geoframe_from_frame(
        frame,
        BuildGeoframeFromFrameConfig(
            x_column="longitude", y_column="latitude", crs="EPSG:4326"
        ),
    )

    assert result["label"].tolist() == ["a", "b", "c"]


def test_step_build_geoframe_from_frame_matches_direct_call() -> None:
    config = BuildGeoframeFromFrameConfig(
        x_column="longitude", y_column="latitude", crs="EPSG:4326"
    )
    frames = {"frame": _frame()}

    from_step: gpd.GeoDataFrame = step_build_geoframe_from_frame(frames, config)
    direct: gpd.GeoDataFrame = build_geoframe_from_frame(
        frames["frame"], config
    )

    assert from_step.equals(direct)
    assert from_step.crs == direct.crs


def test_build_geoframe_from_frame_is_registered() -> None:
    registered = default_registry().get("build_geoframe_from_frame")
    assert registered.processor is step_build_geoframe_from_frame
    assert registered.config_type is BuildGeoframeFromFrameConfig
