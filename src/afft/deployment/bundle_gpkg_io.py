"""Concrete GeoPackage bundle implementing the deployment bundle read-write
`Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import geopandas as gpd
import pandas as pd

from .bundle_gpkg_common import (
    geometry_type,
    layer_exists,
    list_frames,
    list_geoframes,
    read_contents,
    read_frame_table,
    validate_geoframe,
    write_frame_table,
)


@dataclass
class GeoPackageDeploymentBundleIO:
    """Concrete `DeploymentBundleIO` backed by a GeoPackage file."""

    path: Path

    def list_frames(self) -> list[str]:
        return list_frames(self.contents())

    def list_geoframes(self) -> list[str]:
        return list_geoframes(self.contents())

    def has_frame(self, key: str) -> bool:
        return layer_exists(self.path, key)

    def read_frame(self, key: str) -> pd.DataFrame:
        if not self.has_frame(key):
            raise KeyError(key)
        return read_frame_table(self.path, key)

    def is_geoframe(self, key: str) -> bool:
        return geometry_type(self.contents(), key) is not None

    def read_geoframe(self, key: str) -> gpd.GeoDataFrame:
        frame = self.read_frame(key)
        if not isinstance(frame, gpd.GeoDataFrame):
            raise TypeError(f"frame at {key!r} has no geometry column")
        return frame

    def iter_frames(self) -> Iterator[tuple[str, pd.DataFrame]]:
        for key in self.list_frames():
            yield key, self.read_frame(key)

    def iter_geoframes(self) -> Iterator[tuple[str, gpd.GeoDataFrame]]:
        for key in self.list_geoframes():
            yield key, self.read_geoframe(key)

    def contents(self) -> pd.DataFrame:
        return read_contents(self.path)

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if self.has_frame(key) and if_exists == "fail":
            raise ValueError(f"frame already exists at key: {key!r}")
        write_frame_table(self.path, key, frame)

    def write_geoframe(
        self,
        key: str,
        frame: gpd.GeoDataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        validate_geoframe(frame)
        self.write_frame(key, frame, if_exists=if_exists)


@contextmanager
def open_gpkg_deployment_bundle_io(
    path: Path,
) -> Iterator[GeoPackageDeploymentBundleIO]:
    """Open a GeoPackage deployment bundle for reading and writing, creating
    it if absent."""
    yield GeoPackageDeploymentBundleIO(path=path)
