"""Protocol contract tests for the GeoPackage deployment bundle backend.

These exercise only what the `bundle_protocols.py` interfaces promise, and
so run through the public factories rather than the backend module directly.
Backend-specific behaviour belongs in `test_deployment_bundle_gpkg.py`.
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment import (
    DeploymentIdentity,
    open_deployment_bundle,
    open_deployment_bundle_reader,
    open_deployment_bundle_writer,
)
from afft.tasks.build_deployment_bundle import record_to_frame


@pytest.fixture
def bundle_path(tmp_path: Path) -> Path:
    """A bundle path for the GeoPackage backend."""
    return tmp_path / "bundle.gpkg"


def _frame(value: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)],
            "value": [value],
        }
    )


def test_write_and_read_frame_round_trip(bundle_path: Path) -> None:
    """A written frame reads back with the same contents."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("telemetry/raw/dvl_teledyne_navigator/RDI", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        read_back = reader.read_frame(
            "telemetry/raw/dvl_teledyne_navigator/RDI"
        )
        assert read_back["value"].tolist() == [1.0]
        assert read_back["timestamp"].tolist() == [
            pd.Timestamp("2023-10-21 03:00:00", tz="UTC")
        ]


def test_has_frame_and_list_frames(bundle_path: Path) -> None:
    """`has_frame` and `list_frames` reflect what has been written."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        assert not writer.has_frame("bundle")
        writer.write_frame("bundle", _frame())
        writer.write_frame("deployment/identity", _frame())
        assert writer.has_frame("bundle")
        assert writer.has_frame("deployment/identity")
        assert not writer.has_frame("deployment/metadata")

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.has_frame("bundle")
        assert not reader.has_frame("deployment/metadata")
        assert reader.list_frames() == ["bundle", "deployment/identity"]


def test_write_frame_fails_on_existing_key_by_default(
    bundle_path: Path,
) -> None:
    """`write_frame` raises if `key` already exists and `if_exists="fail"`."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())
        with pytest.raises(ValueError):
            writer.write_frame("bundle", _frame())


def test_write_frame_replace_overwrites_existing_key(
    bundle_path: Path,
) -> None:
    """`write_frame(..., if_exists="replace")` overwrites an existing frame."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())
        writer.write_frame("bundle", _frame(2.0), if_exists="replace")

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.read_frame("bundle")["value"].tolist() == [2.0]
        assert reader.list_frames() == ["bundle"]


def test_read_frame_raises_key_error_for_unknown_key(
    bundle_path: Path,
) -> None:
    """Reading a key that was never written raises `KeyError`."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        with pytest.raises(KeyError):
            reader.read_frame("deployment/identity")


def test_contents_manifest_tracks_identifier(bundle_path: Path) -> None:
    """`contents()` lists one row per written frame."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())
        writer.write_frame("deployment/identity", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        contents = reader.contents()
        assert contents["identifier"].tolist() == [
            "bundle",
            "deployment/identity",
        ]


def test_contents_manifest_records_the_geometry_type(bundle_path: Path) -> None:
    """`contents()`'s `geometry_type` column is `None` for a non-spatial
    frame and set for a geospatial one."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        contents = reader.contents()
        assert (
            contents.loc[
                contents["identifier"] == "bundle", "geometry_type"
            ].iloc[0]
            is None
        )


def test_reads_back_a_frame_written_through_the_same_handle(
    bundle_path: Path,
) -> None:
    """A frame is readable from the same open bundle that wrote it."""
    with open_deployment_bundle(bundle_path) as bundle:
        bundle.write_frame("telemetry/raw/pressure", _frame())

        assert bundle.has_frame("telemetry/raw/pressure")
        assert bundle.read_frame("telemetry/raw/pressure")[
            "value"
        ].tolist() == [1.0]


def test_reads_back_a_frame_derived_from_an_earlier_write(
    bundle_path: Path,
) -> None:
    """A frame written from one read is itself readable, as chained steps need."""
    with open_deployment_bundle(bundle_path) as bundle:
        bundle.write_frame("telemetry/raw/pressure", _frame())
        bundle.write_frame(
            "telemetry/processed/pressure",
            bundle.read_frame("telemetry/raw/pressure"),
        )
        bundle.write_frame(
            "telemetry/processed/depth",
            bundle.read_frame("telemetry/processed/pressure"),
        )

        assert bundle.list_frames() == [
            "telemetry/raw/pressure",
            "telemetry/processed/pressure",
            "telemetry/processed/depth",
        ]


def test_written_bundle_is_readable_by_the_reader(bundle_path: Path) -> None:
    """What the read-write bundle writes, the read-only reader reads."""
    with open_deployment_bundle(bundle_path) as bundle:
        bundle.write_frame("telemetry/raw/dvl", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.list_frames() == ["telemetry/raw/dvl"]
        assert reader.read_frame("telemetry/raw/dvl")["value"].tolist() == [1.0]


def test_unsupported_suffix_raises(tmp_path: Path) -> None:
    """Opening a bundle with an unsupported suffix raises."""
    with pytest.raises(NotImplementedError):
        with open_deployment_bundle(tmp_path / "bundle.parquet"):
            pass


@pytest.mark.parametrize(
    "end",
    [
        datetime(2023, 10, 21, 4, 0, 0, tzinfo=timezone.utc),
        None,
    ],
    ids=["clipped", "full-range"],
)
def test_deployment_identity_temporal_range_round_trip(
    bundle_path: Path, end: datetime | None
) -> None:
    """A deployment identity's temporal range survives a round trip.

    Covers both a clipped deployment, which records both bounds, and a
    full-range one, whose absent end is stored as `NaT` in a UTC column
    rather than as a missing column.
    """
    identity = record_to_frame(
        DeploymentIdentity(
            deployment_label="qdch0ftq_20231021_030000",
            deployment_start_datetime=datetime(
                2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc
            ),
            deployment_end_datetime=end,
        )
    )

    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("deployment/identity", identity)

    with open_deployment_bundle_reader(bundle_path) as reader:
        read_back = reader.read_frame("deployment/identity")

    assert read_back["deployment_start_datetime"].iloc[0] == pd.Timestamp(
        "2023-10-21 03:00:00", tz="UTC"
    )
    if end is None:
        assert pd.isna(read_back["deployment_end_datetime"].iloc[0])
    else:
        assert read_back["deployment_end_datetime"].iloc[0] == pd.Timestamp(end)
