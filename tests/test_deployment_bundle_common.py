"""Tests for the storage-agnostic bundle manifest schema and dtype codec."""

import json

from datetime import datetime, timezone

import pandas as pd
import pytest

from afft.deployment.bundle_common import (
    CONTENTS_COLUMNS,
    decode_frame_dtypes,
    empty_contents,
    encode_frame_dtypes,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [datetime(2023, 10, 21, 3, tzinfo=timezone.utc)],
            "count": pd.array([1], dtype="Int64"),
            "measurement": pd.array([1.5], dtype="Float64"),
            "flag": pd.array([True], dtype="boolean"),
            "label": pd.array(["a"], dtype="string"),
            "role": pd.Series(["sensor"], dtype="category"),
        }
    )


def test_empty_contents_has_the_manifest_columns() -> None:
    """An empty manifest carries the columns every backend writes."""
    contents = empty_contents()
    assert tuple(contents.columns) == CONTENTS_COLUMNS
    assert contents.empty


def test_encode_records_the_dtype_of_every_column() -> None:
    """The encoding is a flat column-to-dtype-string JSON object."""
    encoded = json.loads(encode_frame_dtypes(_frame()))
    assert encoded == {
        "timestamp": "datetime64[ns, UTC]",
        "count": "Int64",
        "measurement": "Float64",
        "flag": "boolean",
        "label": "string",
        "role": "category",
    }


def test_dtypes_round_trip_through_the_codec() -> None:
    """Every dtype the encoder writes is one the decoder accepts back."""
    frame = _frame().drop(columns=["role"])
    decoded = decode_frame_dtypes(encode_frame_dtypes(frame))
    assert decoded == dict(frame.dtypes)


def test_category_round_trips_without_its_labels() -> None:
    """`category` records the dtype but not its label set; the labels are
    re-derived from the stored values on read. Ordering is not lossy here
    because `encode_frame_dtypes` refuses ordered categoricals outright."""
    frame = _frame()
    decoded = decode_frame_dtypes(encode_frame_dtypes(frame))

    assert isinstance(decoded["role"], pd.CategoricalDtype)
    assert decoded["role"].categories is None

    # Applied to the values, the labels come back anyway.
    restored = frame.astype({"role": decoded["role"]})
    assert restored["role"].cat.categories.tolist() == ["sensor"]


def test_decoded_dtypes_restore_a_coerced_frame() -> None:
    """The decoded mapping is usable as an `astype` argument, which is how
    a backend with a lossy write path would recover the logical dtypes."""
    frame = _frame()
    encoded = encode_frame_dtypes(frame)

    coerced = frame.astype(
        {"count": "int64", "flag": "bool", "label": "object"}
    )
    restored = coerced.astype(decode_frame_dtypes(encoded))

    assert dict(restored.dtypes) == dict(frame.dtypes)


def test_ordered_categorical_is_refused() -> None:
    """An ordering the encoding cannot represent is rejected at write time
    rather than silently dropped."""
    frame = pd.DataFrame(
        {
            "grade": pd.Series(
                ["low", "high"],
                dtype=pd.CategoricalDtype(["low", "high"], ordered=True),
            )
        }
    )
    with pytest.raises(ValueError, match="ordered categorical"):
        encode_frame_dtypes(frame)


def test_empty_frame_encodes_to_an_empty_object() -> None:
    """A frame with no columns is distinguishable from an absent entry."""
    assert encode_frame_dtypes(pd.DataFrame()) == "{}"
