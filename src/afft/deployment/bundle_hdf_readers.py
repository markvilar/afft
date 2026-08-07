"""Concrete `pandas.HDFStore` reader implementing the deployment bundle
read `Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

_CONTENTS_KEY: str = "bundle_contents"
_RESERVED_KEYS: frozenset[str] = frozenset({_CONTENTS_KEY})


def _read_contents(store: pd.HDFStore) -> pd.DataFrame:
    """Read `bundle_contents`, or an empty frame of the right shape if the
    bundle has no tables."""
    if _CONTENTS_KEY not in store:
        return pd.DataFrame(
            {
                "identifier": pd.array([], dtype="object"),
                "table_name": pd.array([], dtype="object"),
            }
        )
    return store.select(_CONTENTS_KEY)


def _resolve_table_name(store: pd.HDFStore, key: str) -> str:
    """Look up the backend-specific `table_name` for `key` in
    `bundle_contents`.

    Raises
    ------
    KeyError: If no frame is registered under `key`.
    """
    contents = _read_contents(store)
    matches = contents.loc[contents["identifier"] == key, "table_name"]
    if matches.empty:
        raise KeyError(key)
    return str(matches.iloc[0])


@dataclass
class HDFDeploymentBundleReader:
    """Concrete `DeploymentBundleReader` backed by an open `pandas.HDFStore`."""

    store: pd.HDFStore

    def list_frames(self) -> list[str]:
        return list(self.contents()["identifier"])

    def has_frame(self, key: str) -> bool:
        if key in _RESERVED_KEYS:
            return False
        return key in self.list_frames()

    def read_frame(self, key: str) -> pd.DataFrame:
        if key in _RESERVED_KEYS:
            raise KeyError(f"{key!r} is reserved; use contents() instead")
        table_name = _resolve_table_name(self.store, key)
        return self.store.select(table_name)

    def contents(self) -> pd.DataFrame:
        return _read_contents(self.store)


@contextmanager
def open_deployment_bundle_reader(
    path: Path,
) -> Iterator[HDFDeploymentBundleReader]:
    """Open an HDF5 deployment bundle for reading."""
    with pd.HDFStore(str(path), mode="r") as store:
        yield HDFDeploymentBundleReader(store=store)
