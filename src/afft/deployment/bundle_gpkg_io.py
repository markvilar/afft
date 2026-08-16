"""Concrete GeoPackage bundle implementing the deployment bundle read-write
`Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from .bundle_gpkg_common import (
    layer_exists,
    read_contents,
    read_frame_table,
    write_frame_table,
)


@dataclass
class GeoPackageDeploymentBundleIO:
    """Concrete `DeploymentBundleIO` backed by a GeoPackage file."""

    path: Path

    def list_frames(self) -> list[str]:
        return list(self.contents()["identifier"])

    def has_frame(self, key: str) -> bool:
        return layer_exists(self.path, key)

    def read_frame(self, key: str) -> pd.DataFrame:
        if not self.has_frame(key):
            raise KeyError(key)
        return read_frame_table(self.path, key)

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


@contextmanager
def open_deployment_bundle(
    path: Path,
) -> Iterator[GeoPackageDeploymentBundleIO]:
    """Open a GeoPackage deployment bundle for reading and writing, creating
    it if absent."""
    yield GeoPackageDeploymentBundleIO(path=path)
