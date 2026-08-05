"""Concrete `pandas.HDFStore` readers implementing the deployment bundle
read `Protocol` interfaces defined in `bundle_protocols.py`."""

import re

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from pydantic import BaseModel

from .bundle_protocols import TimeWindow
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
    SensorExtrinsics,
    SensorIdentity,
    VesselIdentity,
    VesselSensor,
)

# --- dataclass / pydantic model <- table conversion ---


def frame_to_record[T: BaseModel](frame: pd.DataFrame, cls: type[T]) -> T:
    """
    Decode a one-row `DataFrame` back into an instance of `cls`.

    Arguments
    ---------
    frame: One-row `DataFrame` to decode.
    cls: Model class to validate into.

    Returns
    -------
    The decoded model instance.

    Raises
    ------
    ValueError: If `frame` does not have exactly one row.
    """
    if len(frame) != 1:
        raise ValueError(f"expected exactly one row, got {len(frame)}")
    return cls.model_validate(frame.iloc[0].to_dict())


def frame_to_message_topics(frame: pd.DataFrame) -> list[str]:
    """Decode a `message_topics` table back into an ordered list."""
    return [str(topic) for topic in frame["topic"]]


def frame_to_sensor_calibration(frame: pd.DataFrame) -> SensorCalibration:
    """Decode a `calibration` table back into a `SensorCalibration`."""
    if frame.empty:
        raise ValueError("calibration table has no rows")
    calibration_type = str(frame["calibration_type"].iloc[0])
    parameters = dict(zip(frame["name"], frame["value"], strict=True))
    return SensorCalibration(
        calibration_type=calibration_type, parameters=parameters
    )


def time_window_to_where(window: TimeWindow | None) -> str | None:
    """
    Translate a `TimeWindow` into a PyTables `where=` predicate string
    against the `timestamp` column, or `None` for no predicate.
    """
    if window is None:
        return None
    terms: list[str] = []
    if window.start is not None:
        terms.append(f"timestamp >= '{window.start.isoformat()}'")
    if window.end is not None:
        terms.append(f"timestamp <= '{window.end.isoformat()}'")
    if not terms:
        return None
    return " & ".join(terms)


# --- section readers ---


@dataclass
class HDFDeploymentBundleSectionReader:
    """Reads `deployment/*` from an open store."""

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

    def identity(self) -> DeploymentIdentity:
        return frame_to_record(
            self.store.select(self.identity_path), DeploymentIdentity
        )

    def metadata(self) -> DeploymentMetadata:
        return frame_to_record(
            self.store.select(self.metadata_path), DeploymentMetadata
        )

    def provenance(self) -> DeploymentProvenance:
        return frame_to_record(
            self.store.select(self.provenance_path), DeploymentProvenance
        )

    def files(self) -> pd.DataFrame:
        return self.store.select(self.files_path)


@dataclass
class HDFPlatformBundleSectionReader:
    """Reads `platform/*` from an open store."""

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

    def identity(self) -> PlatformIdentity:
        return frame_to_record(
            self.store.select(self.identity_path), PlatformIdentity
        )

    def sensor_keys(self) -> list[str]:
        return _sensor_keys(self.store, self.root_path)

    def sensors(self) -> list[PlatformSensor]:
        return [
            read_platform_sensor(self.store, key) for key in self.sensor_keys()
        ]


@dataclass
class HDFVesselBundleSectionReader:
    """Reads `vessel/*` from an open store."""

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

    def identity(self) -> VesselIdentity:
        return frame_to_record(
            self.store.select(self.identity_path), VesselIdentity
        )

    def sensor_keys(self) -> list[str]:
        return _sensor_keys(self.store, self.root_path)

    def sensors(self) -> list[VesselSensor]:
        return [
            read_vessel_sensor(self.store, key) for key in self.sensor_keys()
        ]


@dataclass
class HDFRawTelemetryBundleSectionReader:
    """Reads `telemetry/raw/*` from an open store."""

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "telemetry/raw"

    def topic_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/messages"

    def topics(self) -> list[tuple[str, str]]:
        return _topic_pairs(self.store, self.root_path)

    def sensor_keys(self) -> list[str]:
        return sorted({sensor_key for sensor_key, _ in self.topics()})

    def read(
        self, sensor_key: str, topic: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        return self.store.select(
            self.topic_path(sensor_key, topic),
            where=time_window_to_where(window),
        )


@dataclass
class HDFProcessedTelemetryBundleSectionReader:
    """Reads `telemetry/processed/*` from an open store."""

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "telemetry/processed"

    def topic_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/messages"

    def provenance_path(self, sensor_key: str, topic: str) -> str:
        return f"{self.root_path}/{sensor_key}/{topic}/provenance"

    def topics(self) -> list[tuple[str, str]]:
        return _topic_pairs(self.store, self.root_path)

    def sensor_keys(self) -> list[str]:
        return sorted({sensor_key for sensor_key, _ in self.topics()})

    def read(
        self, sensor_key: str, topic: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        return self.store.select(
            self.topic_path(sensor_key, topic),
            where=time_window_to_where(window),
        )

    def provenance(self, sensor_key: str, topic: str) -> ProcessedProvenance:
        return frame_to_record(
            self.store.select(self.provenance_path(sensor_key, topic)),
            ProcessedProvenance,
        )


@dataclass
class HDFTelemetryBundleSectionReader:
    """Composes the raw and processed telemetry readers."""

    raw: HDFRawTelemetryBundleSectionReader
    processed: HDFProcessedTelemetryBundleSectionReader

    def topics(self) -> list[tuple[str, str]]:
        return sorted(set(self.raw.topics()) | set(self.processed.topics()))


@dataclass
class HDFMetoceanBundleSectionReader:
    """Reads `metocean/*` from an open store."""

    store: pd.HDFStore

    @property
    def root_path(self) -> str:
        return "metocean"

    def variable_path(self, provider: str, variable: str) -> str:
        return f"{self.root_path}/{provider}/{variable}"

    def providers(self) -> list[str]:
        pattern = re.compile(rf"^/{re.escape(self.root_path)}/([^/]+)/([^/]+)$")
        return sorted(
            {
                match.group(1)
                for path in self.store.keys()
                if (match := pattern.match(path))
            }
        )

    def variables(self, provider: str) -> list[str]:
        pattern = re.compile(
            rf"^/{re.escape(self.root_path)}/{re.escape(provider)}/([^/]+)$"
        )
        return sorted(
            match.group(1)
            for path in self.store.keys()
            if (match := pattern.match(path))
        )

    def read(
        self, provider: str, variable: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        return self.store.select(
            self.variable_path(provider, variable),
            where=time_window_to_where(window),
        )


# --- top-level reader and its escape hatch ---


@dataclass
class HDFDeploymentBundleReader:
    """
    Concrete `DeploymentBundleReader` backed by a `pandas.HDFStore` opened
    in read mode.

    Attributes
    ----------
    store: Open `HDFStore` handle.
    header: Parsed once at open time, trusted for the rest of the object's
        lifetime.
    """

    store: pd.HDFStore
    header: DeploymentBundleHeader
    deployment: HDFDeploymentBundleSectionReader
    platform: HDFPlatformBundleSectionReader
    vessel: HDFVesselBundleSectionReader
    telemetry: HDFTelemetryBundleSectionReader
    metocean: HDFMetoceanBundleSectionReader

    @property
    def header_path(self) -> str:
        return _HEADER_PATH

    @classmethod
    def open(cls, store: pd.HDFStore) -> "HDFDeploymentBundleReader":
        """Parse the root `bundle` table and wrap the section readers."""
        header = frame_to_record(
            store.select(_HEADER_PATH), DeploymentBundleHeader
        )
        return cls(
            store=store,
            header=header,
            deployment=HDFDeploymentBundleSectionReader(store),
            platform=HDFPlatformBundleSectionReader(store),
            vessel=HDFVesselBundleSectionReader(store),
            telemetry=HDFTelemetryBundleSectionReader(
                raw=HDFRawTelemetryBundleSectionReader(store),
                processed=HDFProcessedTelemetryBundleSectionReader(store),
            ),
            metocean=HDFMetoceanBundleSectionReader(store),
        )

    # flat, path-first escape hatch -- not part of the storage-agnostic
    # Protocol, HDFStore-shaped by nature

    def keys(self) -> list[str]:
        return list(self.store.keys())

    def contains(self, path: str) -> bool:
        return path in self.store

    def row_count(self, path: str) -> int:
        storer = self.store.get_storer(path)
        return int(storer.nrows)

    def read_table(self, path: str) -> pd.DataFrame:
        return self.store.select(path)


@contextmanager
def open_deployment_bundle_reader(
    path: Path,
) -> Iterator[HDFDeploymentBundleReader]:
    """Open an HDF5 deployment bundle for reading."""
    with pd.HDFStore(str(path), mode="r") as store:
        yield HDFDeploymentBundleReader.open(store)


def read_platform_sensor(store: pd.HDFStore, sensor_key: str) -> PlatformSensor:
    """Assemble one `PlatformSensor` from its identity, message_topics,
    extrinsics, and optional calibration nodes."""
    reader = HDFPlatformBundleSectionReader(store)
    return PlatformSensor(
        key=sensor_key,
        message_topics=_maybe_read_message_topics(
            store, reader.sensor_message_topics_path(sensor_key)
        ),
        identity=_maybe_read_record(
            store, reader.sensor_identity_path(sensor_key), SensorIdentity
        ),
        extrinsics=_maybe_read_record(
            store, reader.sensor_extrinsics_path(sensor_key), SensorExtrinsics
        ),
        calibration=_maybe_read_calibration(
            store, reader.sensor_calibration_path(sensor_key)
        ),
    )


def read_vessel_sensor(store: pd.HDFStore, sensor_key: str) -> VesselSensor:
    """Assemble one `VesselSensor` from its identity, message_topics,
    extrinsics, and optional calibration nodes."""
    reader = HDFVesselBundleSectionReader(store)
    return VesselSensor(
        key=sensor_key,
        message_topics=_maybe_read_message_topics(
            store, reader.sensor_message_topics_path(sensor_key)
        ),
        identity=_maybe_read_record(
            store, reader.sensor_identity_path(sensor_key), SensorIdentity
        ),
        extrinsics=_maybe_read_record(
            store, reader.sensor_extrinsics_path(sensor_key), SensorExtrinsics
        ),
        calibration=_maybe_read_calibration(
            store, reader.sensor_calibration_path(sensor_key)
        ),
    )


# --- private helpers ---

_HEADER_PATH: str = "bundle"


def _sensor_keys(store: pd.HDFStore, root_path: str) -> list[str]:
    """List sensor keys under `root_path/sensors/<key>/identity`."""
    pattern = re.compile(rf"^/{re.escape(root_path)}/sensors/([^/]+)/identity$")
    return sorted(
        match.group(1)
        for path in store.keys()
        if (match := pattern.match(path))
    )


def _topic_pairs(store: pd.HDFStore, root_path: str) -> list[tuple[str, str]]:
    """List `(sensor_key, topic)` pairs under `root_path/<key>/<topic>/messages`."""
    pattern = re.compile(rf"^/{re.escape(root_path)}/([^/]+)/([^/]+)/messages$")
    return sorted(
        (match.group(1), match.group(2))
        for path in store.keys()
        if (match := pattern.match(path))
    )


def _maybe_read_record[T: BaseModel](
    store: pd.HDFStore, path: str, cls: type[T]
) -> T | None:
    """Read a flat record at `path`, or `None` if the node is absent."""
    if path not in store:
        return None
    return frame_to_record(store.select(path), cls)


def _maybe_read_message_topics(store: pd.HDFStore, path: str) -> list[str]:
    """Read a `message_topics` table at `path`, or `[]` if the node is
    absent."""
    if path not in store:
        return []
    return frame_to_message_topics(store.select(path))


def _maybe_read_calibration(
    store: pd.HDFStore, path: str
) -> SensorCalibration | None:
    """Read a `calibration` table at `path`, or `None` if the node is
    absent."""
    if path not in store:
        return None
    return frame_to_sensor_calibration(store.select(path))
