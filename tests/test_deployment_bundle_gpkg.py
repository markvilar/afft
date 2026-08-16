"""GeoPackage-specific deployment bundle behaviour.

What the backend shares with every other one is covered by the contract in
`test_deployment_bundle_io.py`. What is left here is the on-disk shape that
makes the bundle legible to tooling other than `afft`, and the value/type
consequences of delegating storage to `geopandas`/`pyogrio` instead of
`sqlite3` directly.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from afft.deployment.bundle_gpkg_io import open_deployment_bundle
from afft.deployment.bundle_gpkg_readers import open_deployment_bundle_reader
from afft.deployment.bundle_gpkg_writers import open_deployment_bundle_writer


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "count": [1, 2],
            "measurement": [1.5, 2.5],
            "label": ["a", "b"],
        }
    )


def test_values_round_trip_faithfully(tmp_path: Path) -> None:
    """Column values read back as written, even though the storage-native
    dtype set differs from the frame's own (see Notes in #285)."""
    path = tmp_path / "bundle.gpkg"
    frame = _frame()

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("telemetry/raw/example/TOPIC", frame)

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("telemetry/raw/example/TOPIC")

    assert read_back["count"].tolist() == [1, 2]
    assert read_back["measurement"].tolist() == [1.5, 2.5]
    assert read_back["label"].tolist() == ["a", "b"]


def test_non_spatial_frame_reads_back_as_a_plain_dataframe(
    tmp_path: Path,
) -> None:
    """A frame with no geometry column is written as a non-spatial layer,
    and reads back as a plain `DataFrame` rather than a `GeoDataFrame`."""
    path = tmp_path / "bundle.gpkg"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", _frame())

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("frame")

    assert not isinstance(read_back, gpd.GeoDataFrame)


def test_index_is_not_stored(tmp_path: Path) -> None:
    """The frame index leaves no stray column behind."""
    path = tmp_path / "bundle.gpkg"
    frame = _frame()

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", frame)

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("frame")

    assert list(read_back.columns) == list(frame.columns)


def test_layer_names_keep_the_frame_identifier_verbatim(
    tmp_path: Path,
) -> None:
    """`/`-containing identifiers become layer names of the same spelling,
    accepted by the GeoPackage driver without modification."""
    path = tmp_path / "bundle.gpkg"
    key = "telemetry/raw/dvl_teledyne_navigator/RDI/messages"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame(key, _frame())

    assert key in gpd.list_layers(path)["name"].values


def test_reader_refuses_a_nonexistent_bundle(tmp_path: Path) -> None:
    """Opening a path that is not there raises rather than treating it as an
    empty bundle."""
    path = tmp_path / "missing.gpkg"

    with pytest.raises(FileNotFoundError):
        with open_deployment_bundle_reader(path):
            pass

    assert not path.exists()


def test_writer_creates_the_bundle_if_absent(tmp_path: Path) -> None:
    """The writer creates the file on first write."""
    path = tmp_path / "bundle.gpkg"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("frame", _frame())

    assert path.exists()


def test_read_write_handle_round_trips_values(tmp_path: Path) -> None:
    """The read-write handle reads back what it wrote through the same
    handle."""
    path = tmp_path / "bundle.gpkg"
    frame = _frame()

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("frame", frame)
        read_back = bundle.read_frame("frame")

    assert read_back["count"].tolist() == frame["count"].tolist()
    assert read_back["label"].tolist() == frame["label"].tolist()
