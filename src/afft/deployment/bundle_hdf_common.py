"""Helpers shared by the `pandas.HDFStore` deployment bundle reader, writer,
and read-write implementations."""

import pandas as pd

from .bundle_common import CONTENTS_KEY, empty_contents


def coerce_storable_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
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


def read_contents(store: pd.HDFStore) -> pd.DataFrame:
    """Read `bundle_contents`, or an empty frame of the right shape if the
    bundle has no tables yet."""
    if CONTENTS_KEY not in store:
        return empty_contents()
    return store.select(CONTENTS_KEY)


def resolve_table_name(store: pd.HDFStore, key: str) -> str:
    """Look up the backend-specific `table_name` for `key` in
    `bundle_contents`.

    Raises
    ------
    KeyError: If no frame is registered under `key`.
    """
    contents = read_contents(store)
    matches = contents.loc[contents["identifier"] == key, "table_name"]
    if matches.empty:
        raise KeyError(key)
    return str(matches.iloc[0])


def upsert_contents_row(
    store: pd.HDFStore, key: str, table_name: str, dtypes: str
) -> None:
    """
    Write the `bundle_contents` row for `key`, creating the manifest table if
    this is the bundle's first frame.

    The row is replaced in place if `key` is already registered, so a frame
    rewritten with a different schema does not leave the manifest describing
    the previous one, and a replacement does not reorder the manifest.

    Arguments
    ---------
    store: Open store to write the manifest into.
    key: The frame's identifier.
    table_name: The frame's backend-specific table name.
    dtypes: The frame's dtypes, encoded by `encode_frame_dtypes`.
    """
    contents = read_contents(store)
    existing = contents.index[contents["identifier"] == key]
    if len(existing):
        updated = contents.copy()
        updated.loc[existing[0], ["table_name", "dtypes"]] = [
            table_name,
            dtypes,
        ]
    else:
        row = pd.DataFrame(
            {
                "identifier": [key],
                "table_name": [table_name],
                "dtypes": [dtypes],
            }
        )
        updated = pd.concat([contents, row], ignore_index=True)
    if CONTENTS_KEY in store:
        store.remove(CONTENTS_KEY)
    store.put(CONTENTS_KEY, updated, format="table")
