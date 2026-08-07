"""Functions turning a structured value (pydantic model, list, `Message`,
`DeploymentFiles`) into a write-ready `DataFrame`, including any
dtype normalization it needs before it can be passed to `write_frame`."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import pandas as pd

from pydantic import BaseModel

from afft.deployment import DeploymentFiles, SensorCalibration
from afft.seabed import Message

_DATETIME_UTC_DTYPE: pd.DatetimeTZDtype = pd.DatetimeTZDtype(
    unit="ns", tz="UTC"
)

_DEPLOYMENT_FILES_REQUIRED_DTYPES: dict[str, str] = {
    "role": "category",
    "path": "object",
}

_RAW_TELEMETRY_REQUIRED_DTYPES: dict[str, str] = {
    "timestamp": str(_DATETIME_UTC_DTYPE),
    "sensor_key": "category",
    "message_topic": "category",
}


def normalize_dtypes(
    frame: pd.DataFrame, dtypes: Mapping[str, str]
) -> pd.DataFrame:
    """
    Cast columns to the HDF5-table-safe dtype set before a `write_frame`.

    Arguments
    ---------
    frame: Frame to normalize; not mutated.
    dtypes: Column name to target dtype string, e.g. ``"category"`` or
        ``"datetime64[ns, UTC]"``.

    Returns
    -------
    A copy of `frame` with the named columns cast.
    """
    frame = frame.copy()
    for column, dtype in dtypes.items():
        if pd.api.types.pandas_dtype(dtype) == _DATETIME_UTC_DTYPE:
            frame[column] = pd.to_datetime(frame[column], utc=True)
        else:
            frame[column] = frame[column].astype(dtype)
    return frame


def record_to_frame(value: BaseModel) -> pd.DataFrame:
    """
    Encode a flat pydantic model as a one-row `DataFrame`.

    Only handles models whose fields are all scalar (`str`, `float`, `int`,
    `bool`, `datetime`) -- a model with a `list`/`dict` field needs its own
    row-per-item table instead, see `message_topics_to_frame` and
    `sensor_calibration_to_frame`. `datetime` fields are detected from the
    model's own field annotations and normalized to `datetime64[ns, UTC]`,
    since `HDFStore`'s `format="table"` cannot write a naive/mixed-tz object
    column.

    Arguments
    ---------
    value: Model instance to encode.

    Returns
    -------
    A one-row `DataFrame`.
    """
    frame = pd.DataFrame([value.model_dump()])
    for name, field in type(value).model_fields.items():
        if field.annotation is datetime:
            frame[name] = pd.to_datetime(frame[name], utc=True)
    return frame


def message_topics_to_frame(topics: list[str]) -> pd.DataFrame:
    """Encode `PlatformSensor`/`VesselSensor` message topics as one row
    per topic."""
    return pd.DataFrame({"topic": pd.array(topics, dtype="object")})


def sensor_calibration_to_frame(value: SensorCalibration) -> pd.DataFrame:
    """
    Encode `SensorCalibration` as one row per parameter, `calibration_type`
    denormalized onto every row so the whole model still lives at a single
    key.
    """
    names = list(value.parameters.keys())
    values = list(value.parameters.values())
    return pd.DataFrame(
        {
            "calibration_type": pd.Categorical(
                [value.calibration_type] * len(names)
            ),
            "name": pd.array(names, dtype="object"),
            "value": pd.array(values, dtype="float64"),
        }
    )


def build_deployment_files_frame(files: DeploymentFiles) -> pd.DataFrame:
    """
    Flatten a deployment's file manifest into one row per file.

    Arguments
    ---------
    files: Resolved file manifest for the deployment.

    Returns
    -------
    Write-ready frame with ``role`` and ``path`` columns, excluding
    ``root`` and ``other``.
    """
    rows: list[dict[str, str]] = []
    for role, value in files.model_dump(exclude={"root", "other"}).items():
        paths: list[Any] = (
            value if isinstance(value, list) else [value] if value else []
        )
        rows.extend({"role": role, "path": str(path)} for path in paths)
    frame = pd.DataFrame(rows)
    _require_columns(
        "deployment/files", frame, list(_DEPLOYMENT_FILES_REQUIRED_DTYPES)
    )
    return normalize_dtypes(frame, _DEPLOYMENT_FILES_REQUIRED_DTYPES)


def build_raw_telemetry_frame(
    sensor_key: str,
    topic: str,
    messages: Sequence[Message[Any, Any]],
) -> pd.DataFrame:
    """
    Encode one topic's parsed raw messages as a write-ready frame.

    Arguments
    ---------
    sensor_key: Curated key of the sensor that emits `topic`.
    topic: Raw message topic the frame's messages belong to.
    messages: Parsed messages for `topic`.

    Returns
    -------
    Write-ready frame with `sensor_key` and `message_topic` columns added,
    dtype-normalized for `telemetry/raw/<sensor_key>/<topic>/messages`.
    """
    frame = pd.DataFrame([message.to_dict() for message in messages])
    frame = frame.rename(columns={"topic": "message_topic"})
    frame["sensor_key"] = sensor_key
    key = f"telemetry/raw/{sensor_key}/{topic}/messages"
    _require_columns(key, frame, list(_RAW_TELEMETRY_REQUIRED_DTYPES))
    _require_utc_datetime(key, frame, "timestamp")
    return normalize_dtypes(frame, _RAW_TELEMETRY_REQUIRED_DTYPES)


def _require_columns(
    key: str, frame: pd.DataFrame, required: list[str]
) -> None:
    """Raise `ValueError` naming `key` and any of `required` missing from
    `frame`, instead of the bare `KeyError` `normalize_dtypes` would
    otherwise raise from indexing a missing column."""
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{key}: missing required column(s): {missing}")


def _require_utc_datetime(key: str, frame: pd.DataFrame, column: str) -> None:
    """Raise `ValueError` if `column` isn't already tz-aware UTC -- the
    specific case `HDFStore.put(..., format="table")` can't write."""
    dtype = frame[column].dtype
    if dtype != _DATETIME_UTC_DTYPE:
        raise ValueError(
            f"{key}: column {column!r} must be tz-aware UTC, got {dtype}"
        )
