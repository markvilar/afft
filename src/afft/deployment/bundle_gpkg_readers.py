"""Concrete GeoPackage reader implementing the deployment bundle read
`Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import geopandas as gpd
import pandas as pd

from .bundle_gpkg_common import (
    geometry_type,
    layer_exists,
    list_frames,
    list_geoframes,
    read_contents,
    read_frame_table,
)
from .bundle_protocols import (
    iter_frames,
    iter_geoframes,
)


@dataclass
class GeoPackageDeploymentBundleReader:
    """Concrete `DeploymentBundleReader` backed by a GeoPackage file."""

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
        return iter_frames(self)

    def iter_geoframes(self) -> Iterator[tuple[str, gpd.GeoDataFrame]]:
        return iter_geoframes(self)

    def contents(self) -> pd.DataFrame:
        return read_contents(self.path)


@contextmanager
def open_gpkg_deployment_bundle_reader(
    path: Path,
) -> Iterator[GeoPackageDeploymentBundleReader]:
    """
    Open a GeoPackage deployment bundle for reading.

    Raises
    ------
    FileNotFoundError: If `path` does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"no deployment bundle at: {path}")
    yield GeoPackageDeploymentBundleReader(path=path)
