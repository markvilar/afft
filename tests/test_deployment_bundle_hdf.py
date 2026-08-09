"""HDF5-specific deployment bundle behaviour.

What the backend shares with every other one is covered by the parametrised
contract in `test_deployment_bundle_io.py`. What is left here is the lossy
write path -- documented properties of this backend, and precisely the
assertions a faithful backend such as SQLite must fail.
"""

import json

from pathlib import Path

import pandas as pd

from afft.deployment.bundle_hdf_readers import open_deployment_bundle_reader
from afft.deployment.bundle_hdf_writers import open_deployment_bundle_writer


def _extension_dtype_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "count": pd.array([1, 2, 3], dtype="Int64"),
            "measurement": pd.array([1.5, 2.5, 3.5], dtype="Float64"),
            "flag": pd.array([True, False, True], dtype="boolean"),
            "label": pd.array(["a", "b", "c"], dtype="string"),
        }
    )


def test_write_frame_coerces_extension_dtypes(tmp_path: Path) -> None:
    """Pandas nullable extension dtypes are coerced to plain-numpy dtypes
    before the underlying `HDFStore.put`, since `format="table"` can't
    store them directly. The values survive; the dtypes do not."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame(
            "telemetry/raw/example/TOPIC", _extension_dtype_frame()
        )

    with open_deployment_bundle_reader(path) as reader:
        read_back = reader.read_frame("telemetry/raw/example/TOPIC")
        assert read_back["count"].tolist() == [1, 2, 3]
        assert read_back["measurement"].tolist() == [1.5, 2.5, 3.5]
        assert read_back["flag"].tolist() == [True, False, True]
        assert read_back["label"].tolist() == ["a", "b", "c"]

        assert read_back["count"].dtype == "int64"
        assert read_back["flag"].dtype == "bool"
        assert read_back["label"].dtype == object


def test_contents_manifest_records_pre_coercion_dtypes(tmp_path: Path) -> None:
    """The manifest records what the frame was written with, so the coercion
    is recorded rather than undone -- the read path stays lossy."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle_writer(path) as writer:
        writer.write_frame("bundle", _extension_dtype_frame())

    with open_deployment_bundle_reader(path) as reader:
        recorded = json.loads(reader.contents()["dtypes"].iloc[0])
        assert recorded["count"] == "Int64"
        assert reader.read_frame("bundle")["count"].dtype == "int64"
