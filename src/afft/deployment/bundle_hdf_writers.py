"""Concrete `pandas.HDFStore` writer implementing the deployment bundle
write `Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

_CONTENTS_KEY: str = "bundle_contents"
_RESERVED_KEYS: frozenset[str] = frozenset({_CONTENTS_KEY})


def _coerce_storable_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Cast pandas extension dtypes (``Int64``, ``Float64``, ``boolean``,
    ``string``) to their plain-numpy equivalents, the dtype set
    `HDFStore.put(..., format="table")` can store.

    Category and timezone-aware datetime columns are left untouched --
    those are exactly the extension dtypes PyTables supports natively.
    Column-specific choices (which columns should be `category` or a
    UTC timestamp) are the caller's responsibility, made before this is
    called.

    Arguments
    ---------
    frame: Frame to coerce; not mutated.

    Returns
    -------
    A copy of `frame` with any nullable numeric/boolean/string columns
    cast to plain numpy dtypes.
    """
    frame = frame.copy()
    for column in frame.columns:
        dtype = frame[column].dtype
        if isinstance(dtype, (pd.CategoricalDtype, pd.DatetimeTZDtype)):
            continue
        if isinstance(dtype, pd.StringDtype):
            frame[column] = frame[column].astype(object)
        elif isinstance(dtype, pd.api.extensions.ExtensionDtype):
            frame[column] = frame[column].astype(dtype.numpy_dtype)
    return frame


def _read_contents(store: pd.HDFStore) -> pd.DataFrame:
    """Read `bundle_contents`, or an empty frame of the right shape if the
    bundle has no tables yet."""
    if _CONTENTS_KEY not in store:
        return pd.DataFrame(
            {
                "identifier": pd.array([], dtype="object"),
                "table_name": pd.array([], dtype="object"),
            }
        )
    return store.select(_CONTENTS_KEY)


def _append_contents_row(store: pd.HDFStore, key: str, table_name: str) -> None:
    """Add one `(identifier, table_name)` row to `bundle_contents`,
    creating the manifest table if this is the bundle's first frame."""
    contents = _read_contents(store)
    row = pd.DataFrame({"identifier": [key], "table_name": [table_name]})
    updated = pd.concat([contents, row], ignore_index=True)
    if _CONTENTS_KEY in store:
        store.remove(_CONTENTS_KEY)
    store.put(_CONTENTS_KEY, updated, format="table")


@dataclass
class HDFDeploymentBundleWriter:
    """Concrete `DeploymentBundleWriter` backed by an open `pandas.HDFStore`."""

    store: pd.HDFStore

    def has_frame(self, key: str) -> bool:
        if key in _RESERVED_KEYS:
            return False
        return key in _read_contents(self.store)["identifier"].values

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if key in _RESERVED_KEYS:
            raise ValueError(f"{key!r} is reserved and managed automatically")

        exists = self.has_frame(key)
        if exists and if_exists == "fail":
            raise ValueError(f"frame already exists at key: {key!r}")

        table_name = key  # HDF: table_name == key verbatim
        frame = _coerce_storable_dtypes(frame)
        if exists:
            self.store.remove(table_name)
        self.store.put(table_name, frame, format="table")

        if not exists:
            _append_contents_row(self.store, key, table_name)


@contextmanager
def open_deployment_bundle_writer(
    path: Path,
) -> Iterator[HDFDeploymentBundleWriter]:
    """Open an HDF5 deployment bundle for writing."""
    with pd.HDFStore(str(path), mode="a") as store:
        yield HDFDeploymentBundleWriter(store=store)
