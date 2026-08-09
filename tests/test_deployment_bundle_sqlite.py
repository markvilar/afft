"""SQLite-specific deployment bundle behaviour.

What the backend shares with every other one is covered by the parametrised
contract in `test_deployment_bundle_io.py`. What is left here is the
faithful round trip the HDF5 backend cannot offer, and the on-disk shape
that makes the bundle legible to tooling other than `afft`.
"""

import sqlite3

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment.bundle_sqlite_io import open_deployment_bundle
from afft.deployment.bundle_sqlite_readers import open_deployment_bundle_reader
from afft.deployment.bundle_sqlite_writers import open_deployment_bundle_writer


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    datetime(
                        2010, 4, 21, 2, 27, 56, 300000, tzinfo=timezone.utc
                    ),
                    None,
                ],
                utc=True,
            ),
            "count": pd.array([1, None], dtype="Int64"),
            "measurement": pd.array([1.5, None], dtype="Float64"),
            "flag": pd.array([True, None], dtype="boolean"),
            "label": pd.array(["a", None], dtype="string"),
            "role": pd.Series(["sensor", None], dtype="category"),
        }
    )


def test_dtypes_round_trip_faithfully(tmp_path: Path) -> None:
    """Every dtype the bundles carry reads back as it was written, missing
    values included -- the difference from the HDF5 backend."""
    path = tmp_path / "bundle.sqlite"
    frame = _frame()

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("telemetry/raw/example/TOPIC", frame)

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("telemetry/raw/example/TOPIC")

    assert dict(read_back.dtypes) == dict(frame.dtypes)
    pd.testing.assert_frame_equal(read_back, frame)


def test_timestamps_are_stored_as_text_with_an_offset(tmp_path: Path) -> None:
    """Timestamps are readable at a SQL prompt without the sidecar, which is
    the point of storing them as ISO text rather than epoch integers."""
    path = tmp_path / "bundle.sqlite"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", _frame())

    connection = sqlite3.connect(path)
    try:
        stored = connection.execute(
            'SELECT typeof(timestamp), timestamp FROM "frame" LIMIT 1'
        ).fetchone()
    finally:
        connection.close()

    assert stored[0] == "text"
    assert stored[1] == "2010-04-21 02:27:56.300000+00:00"


def test_categories_are_stored_as_labels(tmp_path: Path) -> None:
    """A category column is plain readable text on disk, not integer codes
    plus a sidecar table."""
    path = tmp_path / "bundle.sqlite"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", _frame())

    connection = sqlite3.connect(path)
    try:
        stored = connection.execute(
            'SELECT typeof(role), role FROM "frame" LIMIT 1'
        ).fetchone()
    finally:
        connection.close()

    assert stored == ("text", "sensor")


def test_index_is_not_stored(tmp_path: Path) -> None:
    """The frame index leaves no stray column behind."""
    path = tmp_path / "bundle.sqlite"
    frame = _frame()

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", frame)

    connection = sqlite3.connect(path)
    try:
        columns = [
            row[1]
            for row in connection.execute(
                'PRAGMA table_info("frame")'
            ).fetchall()
        ]
    finally:
        connection.close()

    assert columns == list(frame.columns)


def test_table_names_keep_the_frame_identifier_verbatim(
    tmp_path: Path,
) -> None:
    """`/`-containing identifiers become quoted table names of the same
    spelling; a missed quote would surface as an `OperationalError`."""
    path = tmp_path / "bundle.sqlite"
    key = "telemetry/raw/dvl_teledyne_navigator/RDI/messages"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame(key, _frame())

    connection = sqlite3.connect(path)
    try:
        names = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        ]
    finally:
        connection.close()

    assert key in names


def test_reader_refuses_a_nonexistent_bundle(tmp_path: Path) -> None:
    """Opening a path that is not there raises rather than creating an empty
    database, which SQLite would otherwise do silently."""
    path = tmp_path / "missing.sqlite"

    with pytest.raises(FileNotFoundError):
        with open_deployment_bundle_reader(path):
            pass

    assert not path.exists()


def test_writer_creates_the_bundle_if_absent(tmp_path: Path) -> None:
    """The writer creates the file, matching the HDF5 writer's `mode="a"`."""
    path = tmp_path / "bundle.sqlite"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", _frame())

    assert path.exists()


def test_read_write_handle_round_trips_dtypes(tmp_path: Path) -> None:
    """The read-write handle restores dtypes the same way the reader does."""
    path = tmp_path / "bundle.sqlite"
    frame = _frame()

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("frame", frame)
        pd.testing.assert_frame_equal(bundle.read_frame("frame"), frame)
