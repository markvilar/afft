"""Tests for identity resolution and validators shared by both Benthloc
ingestion file builders."""

from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from afft.deployment import (
    open_deployment_bundle_reader,
    open_deployment_bundle,
)

from afft.benthloc import (
    ResolvedIdentity,
    check_crs_is_wgs84,
    check_geometry_is_point_z,
    check_positions_valid_geodetic,
    check_timestamps_monotonically_increasing,
    check_timestamps_tz_aware_utc,
    resolve_identity,
)


def _bundle_with_identity(path: Path) -> Path:
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "platform/identity",
            pd.DataFrame(
                [
                    {
                        "platform_label": "AUV Sirius",
                        "platform_class": "SEABED",
                        "platform_operator": "ACFR",
                    }
                ]
            ),
        )
        bundle.write_frame(
            "deployment/identity",
            pd.DataFrame(
                [
                    {
                        "deployment_label": "r20240101_000000",
                        "deployment_start_datetime": datetime(
                            2024, 1, 1, tzinfo=timezone.utc
                        ),
                        "deployment_end_datetime": None,
                    }
                ]
            ),
        )
    return path


def test_resolve_identity_reads_bundle_identity_when_no_override(
    tmp_path: Path,
) -> None:
    """With no CLI override, both labels come from the bundle."""
    bundle_file = _bundle_with_identity(tmp_path / "bundle.gpkg")

    with open_deployment_bundle_reader(bundle_file) as reader:
        identity = resolve_identity(reader, None, None)

    assert identity == ResolvedIdentity(
        platform_label="AUV Sirius",
        deployment_label="r20240101_000000",
    )


def test_resolve_identity_prefers_override_over_bundle(tmp_path: Path) -> None:
    """A CLI override wins over the bundle's own identity."""
    bundle_file = _bundle_with_identity(tmp_path / "bundle.gpkg")

    with open_deployment_bundle_reader(bundle_file) as reader:
        identity = resolve_identity(reader, "Override Platform", None)

    assert identity.platform_label == "Override Platform"
    assert identity.deployment_label == "r20240101_000000"


def test_resolve_identity_never_reads_bundle_when_both_overridden(
    tmp_path: Path,
) -> None:
    """A bundle with no identity frames still resolves when both labels are
    overridden."""
    with open_deployment_bundle(tmp_path / "bundle.gpkg") as bundle:
        bundle.write_frame("unrelated", pd.DataFrame({"value": [1.0]}))

    with open_deployment_bundle_reader(tmp_path / "bundle.gpkg") as reader:
        identity = resolve_identity(reader, "Platform", "Deployment")

    assert identity == ResolvedIdentity(
        platform_label="Platform", deployment_label="Deployment"
    )


def _geoframe_2d() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"value": [1.0]}, geometry=[Point(1.0, 2.0)], crs="EPSG:4326"
    )


def _geoframe_3d() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"value": [1.0]}, geometry=[Point(1.0, 2.0, 3.0)], crs="EPSG:4326"
    )


def test_check_crs_is_wgs84_accepts_epsg_4326() -> None:
    """No error for a geoframe already in EPSG:4326."""
    check_crs_is_wgs84(_geoframe_3d())


def test_check_crs_is_wgs84_rejects_other_crs() -> None:
    """A different CRS raises rather than being silently accepted."""
    frame = _geoframe_3d().set_crs("EPSG:3857", allow_override=True)
    with pytest.raises(ValueError, match="EPSG:4326"):
        check_crs_is_wgs84(frame)


def test_check_geometry_is_point_z_rejects_2d_points() -> None:
    """A 2D point fails loudly rather than surfacing as an AttributeError
    downstream."""
    with pytest.raises(ValueError, match="Point Z"):
        check_geometry_is_point_z(_geoframe_2d())


def test_check_geometry_is_point_z_accepts_3d_points() -> None:
    check_geometry_is_point_z(_geoframe_3d())


def test_check_positions_valid_geodetic_rejects_out_of_range() -> None:
    frame = gpd.GeoDataFrame(
        {"value": [1.0]}, geometry=[Point(200.0, 2.0, 3.0)], crs="EPSG:4326"
    )
    with pytest.raises(ValueError, match="WGS-84"):
        check_positions_valid_geodetic(frame)


def test_check_timestamps_tz_aware_utc_rejects_naive() -> None:
    naive = pd.Series(pd.to_datetime(["2024-01-01"]))
    with pytest.raises(ValueError, match="timezone-naive"):
        check_timestamps_tz_aware_utc(naive)


def test_check_timestamps_tz_aware_utc_accepts_utc() -> None:
    aware = pd.Series(pd.to_datetime(["2024-01-01"])).dt.tz_localize("UTC")
    check_timestamps_tz_aware_utc(aware)


def test_check_timestamps_monotonically_increasing_rejects_out_of_order() -> (
    None
):
    timestamps = pd.Series(
        pd.to_datetime(["2024-01-02", "2024-01-01"])
    ).dt.tz_localize("UTC")
    with pytest.raises(ValueError, match="monotonically increasing"):
        check_timestamps_monotonically_increasing(timestamps)
