"""Round-trip tests for the pandas.HDFStore deployment bundle implementation."""

import json

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment.bundle_hdf_readers import open_deployment_bundle_reader
from afft.deployment.bundle_hdf_writers import open_deployment_bundle_writer


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)],
            "value": [1.0],
        }
    )


def test_write_and_read_frame_round_trip(tmp_path: Path) -> None:
    """A written frame reads back with the same contents."""
    path = tmp_path / "bundle.h5"
    frame = _frame()

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("telemetry/raw/dvl_teledyne_navigator/RDI", frame)

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame(
            "telemetry/raw/dvl_teledyne_navigator/RDI"
        )
        assert read_back["value"].tolist() == [1.0]


def test_has_frame_and_list_frames(tmp_path: Path) -> None:
    """`has_frame` and `list_frames` reflect what has been written."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        assert not writer.has_frame("bundle")
        writer.write_frame("bundle", _frame())
        writer.write_frame("deployment/identity", _frame())
        assert writer.has_frame("bundle")
        assert writer.has_frame("deployment/identity")
        assert not writer.has_frame("deployment/metadata")

    with open_deployment_bundle_reader(path) as reader:
        assert reader.has_frame("bundle")
        assert not reader.has_frame("deployment/metadata")
        assert reader.list_frames() == ["bundle", "deployment/identity"]


def test_write_frame_fails_on_existing_key_by_default(tmp_path: Path) -> None:
    """`write_frame` raises if `key` already exists and `if_exists="fail"`."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _frame())
        with pytest.raises(ValueError):
            writer.write_frame("bundle", _frame())


def test_write_frame_replace_overwrites_existing_key(tmp_path: Path) -> None:
    """`write_frame(..., if_exists="replace")` overwrites an existing frame."""
    path = tmp_path / "bundle.h5"
    replacement = pd.DataFrame(
        {"timestamp": [_frame()["timestamp"][0]], "value": [2.0]}
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _frame())
        writer.write_frame("bundle", replacement, if_exists="replace")

    with open_deployment_bundle_reader(path) as reader:
        assert reader.read_frame("bundle")["value"].tolist() == [2.0]
        assert reader.list_frames() == ["bundle"]


def test_read_frame_raises_key_error_for_unknown_key(tmp_path: Path) -> None:
    """Reading a key that was never written raises `KeyError`."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _frame())

    with open_deployment_bundle_reader(path) as reader:
        with pytest.raises(KeyError):
            reader.read_frame("deployment/identity")


def test_bundle_contents_is_reserved(tmp_path: Path) -> None:
    """`bundle_contents` cannot be read, written, or reported present through
    the ordinary frame methods -- only `contents()` exposes it."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _frame())
        assert not writer.has_frame("bundle_contents")
        with pytest.raises(ValueError):
            writer.write_frame("bundle_contents", _frame())

    with open_deployment_bundle_reader(path) as reader:
        assert not reader.has_frame("bundle_contents")
        assert "bundle_contents" not in reader.list_frames()
        with pytest.raises(KeyError):
            reader.read_frame("bundle_contents")


def test_contents_manifest_tracks_identifier_and_table_name(
    tmp_path: Path,
) -> None:
    """`contents()` lists one row per written frame, with `identifier` and
    `table_name` equal for the HDF backend."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _frame())
        writer.write_frame("deployment/identity", _frame())

    with open_deployment_bundle_reader(path) as reader:
        contents = reader.contents()
        assert contents["identifier"].tolist() == [
            "bundle",
            "deployment/identity",
        ]
        assert contents["table_name"].tolist() == [
            "bundle",
            "deployment/identity",
        ]


def test_contents_manifest_records_pre_coercion_dtypes(
    tmp_path: Path,
) -> None:
    """The manifest records the dtypes the frame was written with, not the
    plain-numpy ones `coerce_storable_dtypes` reduces them to."""
    path = tmp_path / "bundle.h5"
    frame = pd.DataFrame(
        {
            "count": pd.array([1], dtype="Int64"),
            "flag": pd.array([True], dtype="boolean"),
            "label": pd.array(["a"], dtype="string"),
        }
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", frame)

    with open_deployment_bundle_reader(path) as reader:
        recorded = json.loads(reader.contents()["dtypes"].iloc[0])
        assert recorded == {
            "count": "Int64",
            "flag": "boolean",
            "label": "string",
        }
        # The frame itself still reads back coerced -- the HDF backend
        # records what it discarded without undoing it.
        assert reader.read_frame("bundle")["count"].dtype == "int64"


def test_replacing_a_frame_updates_its_recorded_dtypes(
    tmp_path: Path,
) -> None:
    """A frame rewritten with a different schema leaves no stale manifest
    entry describing the previous one."""
    path = tmp_path / "bundle.h5"
    original = pd.DataFrame({"count": pd.array([1], dtype="Int64")})
    replacement = pd.DataFrame({"label": pd.array(["a"], dtype="string")})

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", original)
        writer.write_frame("bundle", replacement, if_exists="replace")

    with open_deployment_bundle_reader(path) as reader:
        contents = reader.contents()
        assert len(contents) == 1
        assert json.loads(contents["dtypes"].iloc[0]) == {"label": "string"}


def test_replacing_a_frame_preserves_manifest_order(tmp_path: Path) -> None:
    """Replacing a frame updates its row in place rather than moving it to
    the end of the manifest."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("first", _frame())
        writer.write_frame("second", _frame())
        writer.write_frame("first", _frame(), if_exists="replace")

    with open_deployment_bundle_reader(path) as reader:
        assert reader.list_frames() == ["first", "second"]


def test_write_frame_coerces_extension_dtypes(tmp_path: Path) -> None:
    """Pandas nullable extension dtypes are coerced to plain-numpy dtypes
    before the underlying `HDFStore.put`, since `format="table"` can't
    store them directly."""
    path = tmp_path / "bundle.h5"
    frame = pd.DataFrame(
        {
            "count": pd.array([1, 2, 3], dtype="Int64"),
            "measurement": pd.array([1.5, 2.5, 3.5], dtype="Float64"),
            "flag": pd.array([True, False, True], dtype="boolean"),
            "label": pd.array(["a", "b", "c"], dtype="string"),
        }
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("telemetry/raw/example/TOPIC", frame)

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("telemetry/raw/example/TOPIC")
        assert read_back["count"].tolist() == [1, 2, 3]
        assert read_back["measurement"].tolist() == [1.5, 2.5, 3.5]
        assert read_back["flag"].tolist() == [True, False, True]
        assert read_back["label"].tolist() == ["a", "b", "c"]
