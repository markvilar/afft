"""Tests for the Benthloc trajectory ingestion file builder."""

import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from afft.deployment import open_deployment_bundle

from afft.benthloc import (
    BuildTrajectoryIngestionFileCommand,
    BuildTrajectoryIngestionFileResult,
    run_build_trajectory_ingestion_file,
)


def _trajectory_geoframe(
    timestamps: list[str],
    yaw: list[float] | None = None,
) -> gpd.GeoDataFrame:
    count = len(timestamps)
    return gpd.GeoDataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, utc=True),
            "roll": [0.1] * count,
            "pitch": [0.2] * count,
            "yaw": yaw
            if yaw is not None
            else [float(index) for index in range(count)],
        },
        geometry=[
            Point(1.0 + index, 2.0 + index, 3.0 + index)
            for index in range(count)
        ],
        crs="EPSG:4326",
    )


def _bundle(
    path: Path,
    trajectory_key: str = "trajectory/renav_priors/platform_poses",
    trajectory: gpd.GeoDataFrame | None = None,
    with_identity: bool = True,
) -> Path:
    with open_deployment_bundle(path) as bundle:
        bundle.write_geoframe(
            trajectory_key,
            trajectory
            if trajectory is not None
            else _trajectory_geoframe(
                ["2024-01-01T00:00:00Z", "2024-01-01T00:00:01Z"]
            ),
        )
        if with_identity:
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


def _command(
    tmp_path: Path, **overrides: Any
) -> BuildTrajectoryIngestionFileCommand:
    arguments: dict[str, Any] = {
        "bundle_file": overrides.pop("bundle_file", None)
        or _bundle(tmp_path / "bundle.gpkg"),
        "key": "trajectory/renav_priors/platform_poses",
        "output_file": tmp_path / "trajectory.geojson",
        "trajectory_label": "renav_priors",
    }
    arguments.update(overrides)
    return BuildTrajectoryIngestionFileCommand(**arguments)


def test_writes_a_geojson_feature_collection_matching_benthlocs_schema(
    tmp_path: Path,
) -> None:
    """The output file is a FeatureCollection with the exact property set
    Benthloc's reader/builder require."""
    command = _command(tmp_path)

    result = run_build_trajectory_ingestion_file(command)

    assert isinstance(result, BuildTrajectoryIngestionFileResult)
    assert result.written
    assert result.pose_count == 2
    assert result.dropped_row_count == 0
    assert result.platform_label == "AUV Sirius"
    assert result.deployment_label == "r20240101_000000"

    content = json.loads(command.output_file.read_text())
    assert content["type"] == "FeatureCollection"
    assert len(content["features"]) == 2

    feature = content["features"][0]
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 3

    properties = feature["properties"]
    assert set(properties) == {
        "timestamp",
        "platform_label",
        "deployment_label",
        "trajectory_label",
        "trajectory_description",
        "yaw",
        "pitch",
        "roll",
    }
    assert properties["platform_label"] == "AUV Sirius"
    assert properties["deployment_label"] == "r20240101_000000"
    assert properties["trajectory_label"] == "renav_priors"


def test_dry_run_does_not_write_the_output_file(tmp_path: Path) -> None:
    """A dry run reports the labels and pose count without touching disk."""
    command = _command(tmp_path, dry_run=True)

    result = run_build_trajectory_ingestion_file(command)

    assert result.written is False
    assert result.pose_count == 2
    assert not command.output_file.exists()


def test_platform_and_deployment_label_overrides_are_honored(
    tmp_path: Path,
) -> None:
    command = _command(
        tmp_path,
        platform_label="Override Platform",
        deployment_label="override_deployment",
    )

    result = run_build_trajectory_ingestion_file(command)

    assert result.platform_label == "Override Platform"
    assert result.deployment_label == "override_deployment"


def test_missing_bundle_key_raises(tmp_path: Path) -> None:
    """A typo'd key fails clearly rather than reading nothing."""
    command = _command(tmp_path, key="trajectory/absent/platform_poses")

    with pytest.raises(ValueError, match="holds no frame"):
        run_build_trajectory_ingestion_file(command)


def test_non_geoframe_key_raises(tmp_path: Path) -> None:
    """A plain (non-spatial) frame at the key is rejected, not silently
    read as though it had geometry."""
    with open_deployment_bundle(tmp_path / "bundle.gpkg") as bundle:
        bundle.write_frame("trajectory/plain", pd.DataFrame({"value": [1.0]}))

    command = _command(
        tmp_path, bundle_file=tmp_path / "bundle.gpkg", key="trajectory/plain"
    )

    with pytest.raises(TypeError, match="does not hold a geoframe"):
        run_build_trajectory_ingestion_file(command)


def test_wrong_crs_raises(tmp_path: Path) -> None:
    """A CRS other than EPSG:4326 fails here rather than being silently
    reprojected by Benthloc's reader."""
    trajectory = _trajectory_geoframe(
        ["2024-01-01T00:00:00Z", "2024-01-01T00:00:01Z"]
    ).set_crs("EPSG:3857", allow_override=True)
    bundle_file = _bundle(tmp_path / "bundle.gpkg", trajectory=trajectory)

    command = _command(tmp_path, bundle_file=bundle_file)

    with pytest.raises(ValueError, match="EPSG:4326"):
        run_build_trajectory_ingestion_file(command)


def test_non_monotonic_timestamps_raise(tmp_path: Path) -> None:
    trajectory = _trajectory_geoframe(
        ["2024-01-01T00:00:01Z", "2024-01-01T00:00:00Z"]
    )
    bundle_file = _bundle(tmp_path / "bundle.gpkg", trajectory=trajectory)

    command = _command(tmp_path, bundle_file=bundle_file)

    with pytest.raises(ValueError, match="monotonically increasing"):
        run_build_trajectory_ingestion_file(command)


def test_rows_with_null_attitude_are_dropped_and_reported(
    tmp_path: Path,
) -> None:
    """A null yaw/pitch/roll/position/timestamp row is dropped, not
    written, and the drop is reported in the result."""
    trajectory = _trajectory_geoframe(
        [
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:00:01Z",
            "2024-01-01T00:00:02Z",
        ],
        yaw=[1.0, None, 3.0],
    )
    bundle_file = _bundle(tmp_path / "bundle.gpkg", trajectory=trajectory)

    command = _command(tmp_path, bundle_file=bundle_file)

    result = run_build_trajectory_ingestion_file(command)

    assert result.pose_count == 2
    assert result.dropped_row_count == 1


def test_all_rows_dropped_raises(tmp_path: Path) -> None:
    trajectory = _trajectory_geoframe(
        ["2024-01-01T00:00:00Z", "2024-01-01T00:00:01Z"],
        yaw=[None, None],
    )
    bundle_file = _bundle(tmp_path / "bundle.gpkg", trajectory=trajectory)

    command = _command(tmp_path, bundle_file=bundle_file)

    with pytest.raises(ValueError, match="no poses remain"):
        run_build_trajectory_ingestion_file(command)


def test_missing_column_raises_key_error(tmp_path: Path) -> None:
    trajectory = _trajectory_geoframe(
        ["2024-01-01T00:00:00Z", "2024-01-01T00:00:01Z"]
    ).drop(columns=["yaw"])
    bundle_file = _bundle(tmp_path / "bundle.gpkg", trajectory=trajectory)

    command = _command(tmp_path, bundle_file=bundle_file)

    with pytest.raises(KeyError, match="yaw"):
        run_build_trajectory_ingestion_file(command)


def test_output_file_exists_and_overwrite_not_set_raises(
    tmp_path: Path,
) -> None:
    command = _command(tmp_path)
    command.output_file.write_text("existing")

    with pytest.raises(FileExistsError):
        run_build_trajectory_ingestion_file(command)


def test_overwrite_allows_replacing_the_output_file(tmp_path: Path) -> None:
    command = _command(tmp_path)
    command.output_file.write_text("existing")

    result = run_build_trajectory_ingestion_file(
        command.model_copy(update={"overwrite": True})
    )

    assert result.written
