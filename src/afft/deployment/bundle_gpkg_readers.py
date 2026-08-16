"""Concrete GeoPackage reader implementing the deployment bundle read
`Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from .bundle_gpkg_common import (
    layer_exists,
    read_contents,
    read_frame_table,
)


@dataclass
class GeoPackageDeploymentBundleReader:
    """Concrete `DeploymentBundleReader` backed by a GeoPackage file."""

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


@contextmanager
def open_deployment_bundle_reader(
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
