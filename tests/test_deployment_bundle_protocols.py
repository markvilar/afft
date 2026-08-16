"""Conformance tests for the deployment bundle protocols."""

from typing import Literal

import geopandas as gpd
import pandas as pd
import pytest

from afft.deployment import (
    DeploymentBundleIO,
    DeploymentBundleReader,
    DeploymentBundleWriter,
)


class InMemoryBundle:
    """A minimal in-memory bundle satisfying the read and write interfaces."""

    def __init__(self) -> None:
        self._frames: dict[str, pd.DataFrame] = {}

    def list_frames(self) -> list[str]:
        return sorted(self._frames)

    def has_frame(self, key: str) -> bool:
        return key in self._frames

    def read_frame(self, key: str) -> pd.DataFrame:
        if key not in self._frames:
            raise KeyError(key)
        return self._frames[key]

    def is_geoframe(self, key: str) -> bool:
        return isinstance(self.read_frame(key), gpd.GeoDataFrame)

    def read_geoframe(self, key: str) -> gpd.GeoDataFrame:
        frame = self.read_frame(key)
        if not isinstance(frame, gpd.GeoDataFrame):
            raise TypeError(f"frame at {key!r} has no geometry column")
        return frame

    def contents(self) -> pd.DataFrame:
        return pd.DataFrame({"key": self.list_frames()})

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if key in self._frames and if_exists == "fail":
            raise ValueError(f"frame already exists at {key!r}")
        self._frames[key] = frame

    def write_geoframe(
        self,
        key: str,
        frame: gpd.GeoDataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if not isinstance(frame, gpd.GeoDataFrame):
            raise TypeError(f"frame is not a GeoDataFrame: {type(frame)}")
        self.write_frame(key, frame, if_exists=if_exists)


def copy_frame(bundle: DeploymentBundleIO, source: str, target: str) -> None:
    """Read a frame and write it back to another key of the same bundle."""
    bundle.write_frame(target, bundle.read_frame(source))


def read_keys(bundle: DeploymentBundleReader) -> list[str]:
    return bundle.list_frames()


def write_empty(bundle: DeploymentBundleWriter, key: str) -> None:
    bundle.write_frame(key, pd.DataFrame({"value": [1.0]}))


def test_io_supports_reading_back_what_it_wrote() -> None:
    """A bundle passed as `DeploymentBundleIO` reads its own writes."""
    bundle = InMemoryBundle()
    bundle.write_frame("telemetry/raw/pressure", pd.DataFrame({"value": [1.0]}))

    copy_frame(bundle, "telemetry/raw/pressure", "telemetry/processed/pressure")

    assert bundle.has_frame("telemetry/processed/pressure")
    assert bundle.read_frame("telemetry/processed/pressure")[
        "value"
    ].tolist() == [1.0]


def test_io_is_accepted_where_a_single_capability_is_expected() -> None:
    """`DeploymentBundleIO` is usable wherever a reader or writer is."""
    bundle = InMemoryBundle()

    write_empty(bundle, "telemetry/raw/dvl")

    assert read_keys(bundle) == ["telemetry/raw/dvl"]


def test_write_frame_replaces_only_when_asked() -> None:
    """The write interface's `if_exists` contract holds for chained steps."""
    bundle = InMemoryBundle()
    bundle.write_frame(
        "telemetry/processed/dvl", pd.DataFrame({"value": [1.0]})
    )

    with pytest.raises(ValueError):
        bundle.write_frame(
            "telemetry/processed/dvl", pd.DataFrame({"value": [2.0]})
        )

    bundle.write_frame(
        "telemetry/processed/dvl",
        pd.DataFrame({"value": [2.0]}),
        if_exists="replace",
    )

    assert bundle.read_frame("telemetry/processed/dvl")["value"].tolist() == [
        2.0
    ]
