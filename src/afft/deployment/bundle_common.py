"""Storage-agnostic definitions shared by every deployment bundle backend:
the `bundle_contents` manifest schema and the frame dtype codec."""

import json

import pandas as pd

CONTENTS_KEY: str = "bundle_contents"
RESERVED_KEYS: frozenset[str] = frozenset({CONTENTS_KEY})

CONTENTS_COLUMNS: tuple[str, ...] = ("identifier", "table_name", "dtypes")


def empty_contents() -> pd.DataFrame:
    """Build an empty `bundle_contents` manifest with the columns every
    backend writes."""
    return pd.DataFrame(
        {column: pd.array([], dtype="object") for column in CONTENTS_COLUMNS}
    )


def encode_frame_dtypes(frame: pd.DataFrame) -> str:
    """
    Encode a frame's column dtypes as a flat JSON object.

    The values are `str(dtype)` -- ``"Int64"``, ``"datetime64[ns, UTC]"``,
    ``"category"``, and so on -- every one of which `decode_frame_dtypes`
    accepts back. A `category` dtype records neither its label set nor its
    ordering; both are re-derived from the stored values on read.

    Arguments
    ---------
    frame: Frame whose dtypes to record.

    Returns
    -------
    A JSON object mapping column name to dtype string.

    Raises
    ------
    ValueError: If a column is an ordered categorical. The encoding cannot
        represent the ordering, and a backend restoring from it would return
        an unordered categorical whose comparisons raise rather than order --
        a silent change of meaning, so it is refused at write time.
    """
    ordered = [
        str(column)
        for column, dtype in frame.dtypes.items()
        if isinstance(dtype, pd.CategoricalDtype) and dtype.ordered
    ]
    if ordered:
        raise ValueError(
            f"ordered categorical columns cannot be recorded: {ordered}"
        )

    return json.dumps(
        {str(column): str(dtype) for column, dtype in frame.dtypes.items()}
    )


def decode_frame_dtypes(encoded: str) -> dict[str, object]:
    """
    Decode the JSON written by `encode_frame_dtypes` back into pandas dtypes.

    Arguments
    ---------
    encoded: JSON object mapping column name to dtype string.

    Returns
    -------
    Column name to pandas dtype, suitable for `DataFrame.astype`.
    """
    return {
        column: pd.api.types.pandas_dtype(dtype)
        for column, dtype in json.loads(encoded).items()
    }
