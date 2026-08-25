"""Protocol contract tests for the geospatial-aware bundle interface
(`is_geoframe`, `read_geoframe`, `write_geoframe`).

Run through the public factories, like `test_deployment_bundle_io.py`.
Backend-specific geospatial behaviour (CRS round-tripping) belongs in
`test_deployment_bundle_gpkg.py`.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from afft.deployment import (
    open_deployment_bundle_reader,
    open_deployment_bundle_writer,
)


@pytest.fixture
def bundle_path(tmp_path: Path) -> Path:
    return tmp_path / "bundle.gpkg"


def _geoframe() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"value": [1.0, 2.0]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs="EPSG:4326",
    )


def _frame() -> pd.DataFrame:
    return pd.DataFrame({"value": [1.0]})


def test_write_and_read_geoframe_round_trip(bundle_path: Path) -> None:
    """A written geoframe reads back with its geometry and CRS intact."""
    geoframe = _geoframe()

    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("trajectory/renav_priors/camera_poses", geoframe)

    with open_deployment_bundle_reader(bundle_path) as reader:
        read_back = reader.read_geoframe("trajectory/renav_priors/camera_poses")

    assert isinstance(read_back, gpd.GeoDataFrame)
    assert read_back.crs == geoframe.crs
    assert read_back.geometry.tolist() == geoframe.geometry.tolist()


def test_is_geoframe_distinguishes_spatial_from_non_spatial(
    bundle_path: Path,
) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.is_geoframe("geo")
        assert not reader.is_geoframe("plain")


def test_is_geoframe_raises_key_error_for_unknown_key(
    bundle_path: Path,
) -> None:
    """A missing key is a distinct failure from "not geospatial"."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        with pytest.raises(KeyError):
            reader.is_geoframe("missing")


def test_read_geoframe_raises_type_error_for_a_non_spatial_frame(
    bundle_path: Path,
) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        with pytest.raises(TypeError):
            reader.read_geoframe("plain")


def test_read_geoframe_raises_key_error_for_unknown_key(
    bundle_path: Path,
) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        with pytest.raises(KeyError):
            reader.read_geoframe("missing")


def test_write_geoframe_rejects_a_plain_dataframe(bundle_path: Path) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        with pytest.raises(TypeError):
            writer.write_geoframe("plain", _frame())


def test_write_geoframe_rejects_a_geodataframe_with_no_active_geometry(
    bundle_path: Path,
) -> None:
    frame = gpd.GeoDataFrame({"value": [1.0]})

    with open_deployment_bundle_writer(bundle_path) as writer:
        with pytest.raises(TypeError):
            writer.write_geoframe("bad", frame)


def test_write_geoframe_rejects_empty_geometry(bundle_path: Path) -> None:
    frame = gpd.GeoDataFrame({"value": [1.0]}, geometry=[None], crs="EPSG:4326")

    with open_deployment_bundle_writer(bundle_path) as writer:
        with pytest.raises(ValueError):
            writer.write_geoframe("bad", frame)


def test_write_geoframe_rejects_a_missing_crs(bundle_path: Path) -> None:
    frame = gpd.GeoDataFrame({"value": [1.0]}, geometry=[Point(0, 0)])

    with open_deployment_bundle_writer(bundle_path) as writer:
        with pytest.raises(ValueError):
            writer.write_geoframe("bad", frame)


def test_write_geoframe_replace_overwrites_existing_key(
    bundle_path: Path,
) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        replacement = gpd.GeoDataFrame(
            {"value": [9.0]}, geometry=[Point(9, 9)], crs="EPSG:4326"
        )
        writer.write_geoframe("geo", replacement, if_exists="replace")

    with open_deployment_bundle_reader(bundle_path) as reader:
        read_back = reader.read_geoframe("geo")
        assert read_back["value"].tolist() == [9.0]


def test_write_geoframe_fails_on_existing_key_by_default(
    bundle_path: Path,
) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        with pytest.raises(ValueError):
            writer.write_geoframe("geo", _geoframe())


def test_list_frames_and_list_geoframes_partition_the_bundle(
    bundle_path: Path,
) -> None:
    """`list_frames` and `list_geoframes` are disjoint and, together, cover
    every key the bundle holds."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.list_frames() == ["plain"]
        assert reader.list_geoframes() == ["geo"]
        assert set(reader.list_frames()) & set(reader.list_geoframes()) == set()
        assert set(reader.list_frames()) | set(reader.list_geoframes()) == set(
            reader.contents()["identifier"]
        )


def test_iter_frames_yields_only_plain_frames(bundle_path: Path) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        pairs = list(reader.iter_frames())

    assert [key for key, _ in pairs] == ["plain"]
    assert pairs[0][1]["value"].tolist() == [1.0]


def test_iter_geoframes_yields_only_geoframes(bundle_path: Path) -> None:
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_geoframe("geo", _geoframe())
        writer.write_frame("plain", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        pairs = list(reader.iter_geoframes())

    assert [key for key, _ in pairs] == ["geo"]
    assert isinstance(pairs[0][1], gpd.GeoDataFrame)
    assert pairs[0][1].crs == _geoframe().crs
