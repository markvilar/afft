"""Round-trip tests for the pandas.HDFStore read-write deployment bundle."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment import (
    open_deployment_bundle,
    open_deployment_bundle_reader,
)


def _frame(value: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)],
            "value": [value],
        }
    )


def test_reads_back_a_frame_written_through_the_same_handle(
    tmp_path: Path,
) -> None:
    """A frame is readable from the same open bundle that wrote it."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("telemetry/raw/pressure", _frame())

        assert bundle.has_frame("telemetry/raw/pressure")
        assert bundle.read_frame("telemetry/raw/pressure")[
            "value"
        ].tolist() == [1.0]


def test_reads_back_a_frame_derived_from_an_earlier_write(
    tmp_path: Path,
) -> None:
    """A frame written from one read is itself readable, as chained steps need."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle(path) as bundle:
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


def test_replaces_a_frame_it_wrote_earlier(tmp_path: Path) -> None:
    """`if_exists="replace"` overwrites in place without duplicating contents."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("telemetry/raw/dvl", _frame())

        with pytest.raises(ValueError):
            bundle.write_frame("telemetry/raw/dvl", _frame(2.0))

        bundle.write_frame(
            "telemetry/raw/dvl", _frame(2.0), if_exists="replace"
        )

        assert bundle.read_frame("telemetry/raw/dvl")["value"].tolist() == [2.0]
        assert bundle.list_frames() == ["telemetry/raw/dvl"]


def test_written_bundle_is_readable_by_the_reader(tmp_path: Path) -> None:
    """What the read-write bundle writes, the read-only reader reads."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("telemetry/raw/dvl", _frame())

    with open_deployment_bundle_reader(path) as reader:
        assert reader.list_frames() == ["telemetry/raw/dvl"]
        assert reader.read_frame("telemetry/raw/dvl")["value"].tolist() == [1.0]


def test_read_frame_raises_key_error_for_unknown_key(tmp_path: Path) -> None:
    """Reading a key that was never written raises `KeyError`."""
    path = tmp_path / "bundle.h5"

    with open_deployment_bundle(path) as bundle:
        bundle.write_frame("telemetry/raw/dvl", _frame())

        with pytest.raises(KeyError):
            bundle.read_frame("telemetry/processed/dvl")


def test_unsupported_suffix_raises(tmp_path: Path) -> None:
    """Opening a bundle with an unsupported suffix raises."""
    with pytest.raises(NotImplementedError):
        with open_deployment_bundle(tmp_path / "bundle.parquet"):
            pass
