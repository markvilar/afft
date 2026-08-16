"""Concrete GeoPackage writer implementing the deployment bundle write
`Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from .bundle_gpkg_common import layer_exists, write_frame_table


@dataclass
class GeoPackageDeploymentBundleWriter:
    """Concrete `DeploymentBundleWriter` backed by a GeoPackage file."""

    path: Path

    def has_frame(self, key: str) -> bool:
        return layer_exists(self.path, key)

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
def open_gpkg_deployment_bundle_writer(
    path: Path,
) -> Iterator[GeoPackageDeploymentBundleWriter]:
    """Open a GeoPackage deployment bundle for writing, creating it if
    absent."""
    yield GeoPackageDeploymentBundleWriter(path=path)
