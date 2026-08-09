"""Protocol contract tests, run against every deployment bundle backend.

These exercise only what the `bundle_protocols.py` interfaces promise, and
so are parametrised over each supported file suffix through the public
factories. Backend-specific behaviour belongs in the per-backend modules.
"""

import json

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment import (
    open_deployment_bundle,
    open_deployment_bundle_reader,
    open_deployment_bundle_writer,
)

SUFFIXES: tuple[str, ...] = (".h5", ".sqlite")


@pytest.fixture(params=SUFFIXES)
def bundle_path(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """A bundle path for each supported storage backend."""
    return tmp_path / f"bundle{request.param}"


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


def test_bundle_contents_is_reserved(bundle_path: Path) -> None:
    """`bundle_contents` cannot be read, written, or reported present through
    the ordinary frame methods -- only `contents()` exposes it."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())
        assert not writer.has_frame("bundle_contents")
        with pytest.raises(ValueError):
            writer.write_frame("bundle_contents", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert not reader.has_frame("bundle_contents")
        assert "bundle_contents" not in reader.list_frames()
        with pytest.raises(KeyError):
            reader.read_frame("bundle_contents")


def test_contents_manifest_tracks_identifier_and_table_name(
    bundle_path: Path,
) -> None:
    """`contents()` lists one row per written frame, with `identifier` and
    `table_name` equal for both backends."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", _frame())
        writer.write_frame("deployment/identity", _frame())

    with open_deployment_bundle_reader(bundle_path) as reader:
        contents = reader.contents()
        assert contents["identifier"].tolist() == [
            "bundle",
            "deployment/identity",
        ]
        assert contents["table_name"].tolist() == [
            "bundle",
            "deployment/identity",
        ]


def test_contents_manifest_records_the_frame_dtypes(
    bundle_path: Path,
) -> None:
    """The manifest records the dtypes the frame was written with, whatever
    the backend then does with them."""
    frame = pd.DataFrame(
        {
            "count": pd.array([1], dtype="Int64"),
            "flag": pd.array([True], dtype="boolean"),
            "label": pd.array(["a"], dtype="string"),
        }
    )

    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", frame)

    with open_deployment_bundle_reader(bundle_path) as reader:
        recorded = json.loads(reader.contents()["dtypes"].iloc[0])
        assert recorded == {
            "count": "Int64",
            "flag": "boolean",
            "label": "string",
        }


def test_replacing_a_frame_updates_its_recorded_dtypes(
    bundle_path: Path,
) -> None:
    """A frame rewritten with a different schema leaves no stale manifest
    entry describing the previous one."""
    original = pd.DataFrame({"count": pd.array([1], dtype="Int64")})
    replacement = pd.DataFrame({"label": pd.array(["a"], dtype="string")})

    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("bundle", original)
        writer.write_frame("bundle", replacement, if_exists="replace")

    with open_deployment_bundle_reader(bundle_path) as reader:
        contents = reader.contents()
        assert len(contents) == 1
        assert json.loads(contents["dtypes"].iloc[0]) == {"label": "string"}


def test_replacing_a_frame_preserves_manifest_order(
    bundle_path: Path,
) -> None:
    """Replacing a frame updates its row in place rather than moving it to
    the end of the manifest."""
    with open_deployment_bundle_writer(bundle_path) as writer:
        writer.write_frame("first", _frame())
        writer.write_frame("second", _frame())
        writer.write_frame("first", _frame(), if_exists="replace")

    with open_deployment_bundle_reader(bundle_path) as reader:
        assert reader.list_frames() == ["first", "second"]


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
