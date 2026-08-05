"""Concrete `pandas.HDFStore` writers implementing the deployment bundle
write `Protocol` interfaces defined in `bundle_protocols.py`."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

import pandas as pd

from pydantic import BaseModel

from .bundle_types import (
    DeploymentBundleHeader,
    DeploymentIdentity,
    DeploymentProvenance,
    ProcessedProvenance,
)
from .common_types import (
    DeploymentMetadata,
    PlatformIdentity,
    PlatformSensor,
    SensorCalibration,
    VesselIdentity,
    VesselSensor,
)

# --- dtype normalization and put policy helpers ---


def normalize_dtypes(
    frame: pd.DataFrame, dtypes: Mapping[str, str]
) -> pd.DataFrame:
    """
    Cast columns to the HDF5-table-safe dtype set before a `put`/`append`.

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
        if dtype == "datetime64[ns, UTC]":
            frame[column] = pd.to_datetime(frame[column], utc=True)
        else:
            frame[column] = frame[column].astype(dtype)
    return frame


def put_once(
    store: pd.HDFStore,
    path: str,
    frame: pd.DataFrame,
    *,
    data_columns: list[str] | None = None,
) -> None:
    """
    `store.put` a table at `path`, raising if a node already exists there.

    Arguments
    ---------
    store: Open `HDFStore` handle.
    path: Node path to write.
    frame: Table to write.
    data_columns: Columns to index for `where=` queries.

    Raises
    ------
    ValueError: If a node already exists at `path`.
    """
    if path in store:
        raise ValueError(f"{path} already exists")
    store.put(path, frame, format="table", data_columns=data_columns)


def put_replacing(
    store: pd.HDFStore,
    path: str,
    frame: pd.DataFrame,
    *,
    data_columns: list[str] | None = None,
) -> None:
    """
    `store.remove` any existing node at `path`, then `store.put` the new
    frame.

    Arguments
    ---------
    store: Open `HDFStore` handle.
    path: Node path to write.
    frame: Table to write.
    data_columns: Columns to index for `where=` queries.
    """
    if path in store:
        store.remove(path)
    store.put(path, frame, format="table", data_columns=data_columns)


# --- dataclass / pydantic model -> table conversion ---


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
    """Encode `CatalogProfileSensor.message_topics` as one row per topic."""
    return pd.DataFrame({"topic": pd.array(topics, dtype="object")})


def sensor_calibration_to_frame(value: SensorCalibration) -> pd.DataFrame:
    """
    Encode `SensorCalibration` as one row per parameter, `calibration_type`
    denormalized onto every row so the whole model still lives at a single
    path.
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


# --- section writers ---


@dataclass
class HDFDeploymentBundleSectionWriter:
    """
    Writes `deployment/*` to an open store.

    Each method is write-once -- it raises if the target node already
    exists.
    """

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "deployment"

    @property
    def identity_path(self) -> str:
        return f"{self.root_path}/identity"

    @property
    def metadata_path(self) -> str:
        return f"{self.root_path}/metadata"

    @property
    def files_path(self) -> str:
        return f"{self.root_path}/files"

    @property
    def provenance_path(self) -> str:
        return f"{self.root_path}/provenance"

    def write_identity(self, value: DeploymentIdentity) -> None:
        put_once(self.store, self.identity_path, record_to_frame(value))

    def write_metadata(self, value: DeploymentMetadata) -> None:
        put_once(self.store, self.metadata_path, record_to_frame(value))

    def write_files(self, frame: pd.DataFrame) -> None:
        frame = normalize_dtypes(frame, _DEPLOYMENT_FILES_REQUIRED_DTYPES)
        put_once(self.store, self.files_path, frame, data_columns=["role"])

    def write_provenance(self, value: DeploymentProvenance) -> None:
        put_once(self.store, self.provenance_path, record_to_frame(value))


@dataclass
class HDFPlatformBundleSectionWriter:
    """
    Writes `platform/*` to an open store.

    Each method is write-once -- it raises if the target node already
    exists. A sensor's optional `identity`/`extrinsics`/`calibration` node,
    or its `message_topics` node when the list is empty, is simply not
    written rather than written empty; the reader treats a missing node as
    `None`/`[]`.
    """

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "platform"

    @property
    def identity_path(self) -> str:
        return f"{self.root_path}/identity"

    def sensor_identity_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/identity"

    def sensor_message_topics_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/message_topics"

    def sensor_extrinsics_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/extrinsics"

    def sensor_calibration_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/calibration"

    def write_identity(self, value: PlatformIdentity) -> None:
        put_once(self.store, self.identity_path, record_to_frame(value))

    def write_sensors(self, values: list[PlatformSensor]) -> None:
        for sensor in values:
            _write_sensor(self, sensor)


@dataclass
class HDFVesselBundleSectionWriter:
    """
    Writes `vessel/*` to an open store.

    Each method is write-once -- it raises if the target node already
    exists. A sensor's optional `identity`/`extrinsics`/`calibration` node,
    or its `message_topics` node when the list is empty, is simply not
    written rather than written empty; the reader treats a missing node as
    `None`/`[]`.
    """

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "vessel"

    @property
    def identity_path(self) -> str:
        return f"{self.root_path}/identity"

    def sensor_identity_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/identity"

    def sensor_message_topics_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/message_topics"

    def sensor_extrinsics_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/extrinsics"

    def sensor_calibration_path(self, sensor_key: str) -> str:
        return f"{self.root_path}/sensors/{sensor_key}/calibration"

    def write_identity(self, value: VesselIdentity) -> None:
        put_once(self.store, self.identity_path, record_to_frame(value))

    def write_sensors(self, values: list[VesselSensor]) -> None:
        for sensor in values:
            _write_sensor(self, sensor)


@dataclass
class HDFRawTelemetryBundleSectionWriter:
    """
    Writes `telemetry/raw/*` to an open store.

    Write-once -- it raises if the target node already exists.
    """

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "telemetry/raw"

    def topic_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/messages"

    def write(self, sensor_key: str, topic: str, frame: pd.DataFrame) -> None:
        frame = normalize_dtypes(frame, _RAW_TELEMETRY_REQUIRED_DTYPES)
        put_once(
            self.store,
            self.topic_path(sensor_key, topic),
            frame,
            data_columns=list(_RAW_TELEMETRY_REQUIRED_DTYPES),
        )


@dataclass
class HDFProcessedTelemetryBundleSectionWriter:
    """Writes `telemetry/processed/*` to an open store."""

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "telemetry/processed"

    def topic_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/messages"

    def provenance_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/provenance"

    def append_messages(
        self, sensor_key: str, topic: str, frame: pd.DataFrame
    ) -> None:
        dtypes = _processed_telemetry_dtypes(frame)
        frame = normalize_dtypes(frame, dtypes)
        self.store.append(
            self.topic_path(sensor_key, topic),
            frame,
            format="table",
            data_columns=list(dtypes),
        )

    def replace_messages(
        self, sensor_key: str, topic: str, frame: pd.DataFrame
    ) -> None:
        dtypes = _processed_telemetry_dtypes(frame)
        frame = normalize_dtypes(frame, dtypes)
        put_replacing(
            self.store,
            self.topic_path(sensor_key, topic),
            frame,
            data_columns=list(dtypes),
        )

    def write_provenance(
        self, sensor_key: str, topic: str, value: ProcessedProvenance
    ) -> None:
        put_replacing(
            self.store,
            self.provenance_path(sensor_key, topic),
            record_to_frame(value),
        )


@dataclass
class HDFTelemetryBundleSectionWriter:
    """Composes the raw and processed telemetry writers."""

    raw: HDFRawTelemetryBundleSectionWriter
    processed: HDFProcessedTelemetryBundleSectionWriter


@dataclass
class HDFMetoceanBundleSectionWriter:
    """
    Writes `metocean/*` to an open store.

    Write-once -- it raises if the target node already exists.
    """

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "metocean"

    def variable_path(self, provider: str, variable: str) -> str:
        return f"{self.root_path}/{provider}/{variable}"

    def write(self, provider: str, variable: str, frame: pd.DataFrame) -> None:
        put_once(self.store, self.variable_path(provider, variable), frame)


# --- top-level writer ---


@dataclass
class HDFDeploymentBundleWriter:
    """Concrete `DeploymentBundleWriter` backed by a `pandas.HDFStore`
    opened in write/append mode."""

    store: pd.HDFStore
    deployment: HDFDeploymentBundleSectionWriter
    platform: HDFPlatformBundleSectionWriter
    vessel: HDFVesselBundleSectionWriter
    telemetry: HDFTelemetryBundleSectionWriter
    metocean: HDFMetoceanBundleSectionWriter

    @property
    def header_path(self) -> str:
        return _HEADER_PATH

    def write_header(self, value: DeploymentBundleHeader) -> None:
        put_once(self.store, self.header_path, record_to_frame(value))


@contextmanager
def open_deployment_bundle_writer(
    path: Path,
) -> Iterator[HDFDeploymentBundleWriter]:
    """Open an HDF5 deployment bundle for writing."""
    with pd.HDFStore(str(path), mode="a") as store:
        yield HDFDeploymentBundleWriter(
            store=store,
            deployment=HDFDeploymentBundleSectionWriter(store),
            platform=HDFPlatformBundleSectionWriter(store),
            vessel=HDFVesselBundleSectionWriter(store),
            telemetry=HDFTelemetryBundleSectionWriter(
                raw=HDFRawTelemetryBundleSectionWriter(store),
                processed=HDFProcessedTelemetryBundleSectionWriter(store),
            ),
            metocean=HDFMetoceanBundleSectionWriter(store),
        )


# --- private helpers ---

_HEADER_PATH: str = "bundle"

_RAW_TELEMETRY_REQUIRED_DTYPES: dict[str, str] = {
    "timestamp": "datetime64[ns, UTC]",
    "sensor_key": "category",
    "message_topic": "category",
}

_PROCESSED_TELEMETRY_REQUIRED_DTYPES: dict[str, str] = {
    "timestamp": "datetime64[ns, UTC]",
    "message_topic": "category",
}

_DEPLOYMENT_FILES_REQUIRED_DTYPES: dict[str, str] = {
    "role": "category",
    "path": "object",
}


def _processed_telemetry_dtypes(frame: pd.DataFrame) -> dict[str, str]:
    """Required processed-telemetry dtypes, including `sensor_key` only
    when the frame carries that column -- it's required only for a table
    with one producing sensor."""
    dtypes = dict(_PROCESSED_TELEMETRY_REQUIRED_DTYPES)
    if "sensor_key" in frame.columns:
        dtypes["sensor_key"] = "category"
    return dtypes


def _write_sensor(
    writer: "HDFPlatformBundleSectionWriter | HDFVesselBundleSectionWriter",
    sensor: PlatformSensor | VesselSensor,
) -> None:
    """Write a sensor's identity/message_topics/extrinsics/calibration
    nodes, skipping any field that is `None`/empty."""
    if sensor.identity is not None:
        put_once(
            writer.store,
            writer.sensor_identity_path(sensor.key),
            record_to_frame(sensor.identity),
        )
    if sensor.message_topics:
        put_once(
            writer.store,
            writer.sensor_message_topics_path(sensor.key),
            message_topics_to_frame(sensor.message_topics),
        )
    if sensor.extrinsics is not None:
        put_once(
            writer.store,
            writer.sensor_extrinsics_path(sensor.key),
            record_to_frame(sensor.extrinsics),
        )
    if sensor.calibration is not None:
        put_once(
            writer.store,
            writer.sensor_calibration_path(sensor.key),
            sensor_calibration_to_frame(sensor.calibration),
            data_columns=["calibration_type"],
        )
