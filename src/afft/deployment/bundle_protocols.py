"""Storage-agnostic read and write interfaces for a deployment bundle."""

from datetime import datetime
from typing import Protocol

import pandas as pd

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
    VesselIdentity,
    VesselSensor,
)


class TimeWindow(Protocol):
    """
    A time range for narrowing a telemetry or metocean read, replacing a
    PyTables ``where=`` string so the interface never speaks PyTables query
    syntax.

    Attributes
    ----------
    start: Start of the window; unbounded below when ``None``.
    end: End of the window; unbounded above when ``None``.
    """

    start: datetime | None
    end: datetime | None


class DeploymentBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``deployment`` section."""

    def identity(self) -> DeploymentIdentity:
        """Read ``deployment/identity``."""
        ...

    def metadata(self) -> DeploymentMetadata:
        """Read ``deployment/metadata``."""
        ...

    def provenance(self) -> DeploymentProvenance:
        """Read ``deployment/provenance``."""
        ...

    def files(self) -> pd.DataFrame:
        """Read ``deployment/files``."""
        ...


class PlatformBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``platform`` section."""

    def identity(self) -> PlatformIdentity:
        """Read ``platform/identity``."""
        ...

    def sensor_keys(self) -> list[str]:
        """List the platform's sensor keys."""
        ...

    def sensors(self) -> list[PlatformSensor]:
        """
        Read the platform's sensor roster.

        Each returned sensor already carries its identity, message topics,
        extrinsics, and calibration.
        """
        ...


class VesselBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``vessel`` section."""

    def identity(self) -> VesselIdentity:
        """Read ``vessel/identity``."""
        ...

    def sensor_keys(self) -> list[str]:
        """List the vessel's sensor keys."""
        ...

    def sensors(self) -> list[VesselSensor]:
        """
        Read the vessel's sensor roster.

        Each returned sensor already carries its identity, message topics,
        extrinsics, and calibration.
        """
        ...


class RawTelemetryBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``telemetry/raw`` section."""

    def topics(self) -> list[tuple[str, str]]:
        """List the ``(sensor_key, message_topic)`` pairs present."""
        ...

    def sensor_keys(self) -> list[str]:
        """List the sensor keys with raw telemetry present."""
        ...

    def read(
        self, sensor_key: str, topic: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        """Read one raw telemetry table, optionally narrowed to a window."""
        ...


class ProcessedTelemetryBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``telemetry/processed`` section."""

    def topics(self) -> list[tuple[str, str]]:
        """List the ``(sensor_key, message_topic)`` pairs present."""
        ...

    def sensor_keys(self) -> list[str]:
        """List the sensor keys with processed telemetry present, including ``"_derived"``."""
        ...

    def read(
        self, sensor_key: str, topic: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        """Read one processed telemetry table, optionally narrowed to a window."""
        ...

    def provenance(self, sensor_key: str, topic: str) -> ProcessedProvenance:
        """Read the provenance of one processed telemetry table."""
        ...


class TelemetryBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``telemetry`` section."""

    raw: RawTelemetryBundleSectionReader
    processed: ProcessedTelemetryBundleSectionReader

    def topics(self) -> list[tuple[str, str]]:
        """List the ``(sensor_key, message_topic)`` pairs present across raw and processed."""
        ...


class MetoceanBundleSectionReader(Protocol):
    """Read accessor for a bundle's ``metocean`` section."""

    def providers(self) -> list[str]:
        """List the metocean providers present."""
        ...

    def variables(self, provider: str) -> list[str]:
        """List the variables present for one provider."""
        ...

    def read(
        self, provider: str, variable: str, *, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        """Read one metocean table, optionally narrowed to a window."""
        ...


class DeploymentBundleReader(Protocol):
    """Read interface for a deployment bundle."""

    header: DeploymentBundleHeader
    deployment: DeploymentBundleSectionReader
    platform: PlatformBundleSectionReader
    vessel: VesselBundleSectionReader
    telemetry: TelemetryBundleSectionReader
    metocean: MetoceanBundleSectionReader


class DeploymentBundleSectionWriter(Protocol):
    """
    Write primitives for a bundle's ``deployment`` section.

    Each method is write-once — it raises if the target node already exists.
    """

    def write_identity(self, value: DeploymentIdentity) -> None:
        """Write ``deployment/identity``."""
        ...

    def write_metadata(self, value: DeploymentMetadata) -> None:
        """Write ``deployment/metadata``."""
        ...

    def write_files(self, frame: pd.DataFrame) -> None:
        """Write ``deployment/files``."""
        ...

    def write_provenance(self, value: DeploymentProvenance) -> None:
        """Write ``deployment/provenance``."""
        ...


class PlatformBundleSectionWriter(Protocol):
    """
    Write primitives for a bundle's ``platform`` section.

    Each method is write-once — it raises if the target node already exists.
    """

    def write_identity(self, value: PlatformIdentity) -> None:
        """Write ``platform/identity``."""
        ...

    def write_sensors(self, values: list[PlatformSensor]) -> None:
        """Write the platform's sensor roster."""
        ...


class VesselBundleSectionWriter(Protocol):
    """
    Write primitives for a bundle's ``vessel`` section.

    Each method is write-once — it raises if the target node already exists.
    """

    def write_identity(self, value: VesselIdentity) -> None:
        """Write ``vessel/identity``."""
        ...

    def write_sensors(self, values: list[VesselSensor]) -> None:
        """Write the vessel's sensor roster."""
        ...


class RawTelemetryBundleSectionWriter(Protocol):
    """
    Write primitive for a bundle's ``telemetry/raw`` section.

    Write-once — it raises if the target node already exists.
    """

    def write(self, sensor_key: str, topic: str, frame: pd.DataFrame) -> None:
        """Write one raw telemetry table."""
        ...


class ProcessedTelemetryBundleSectionWriter(Protocol):
    """Write primitives for a bundle's ``telemetry/processed`` section."""

    def append_messages(
        self, sensor_key: str, topic: str, frame: pd.DataFrame
    ) -> None:
        """Append rows to one processed telemetry table."""
        ...

    def replace_messages(
        self, sensor_key: str, topic: str, frame: pd.DataFrame
    ) -> None:
        """Replace one processed telemetry table."""
        ...

    def write_provenance(
        self, sensor_key: str, topic: str, value: ProcessedProvenance
    ) -> None:
        """Write the provenance for one processed telemetry table, creating
        it if absent or overwriting it if present."""
        ...


class TelemetryBundleSectionWriter(Protocol):
    """Write primitives for a bundle's ``telemetry`` section."""

    raw: RawTelemetryBundleSectionWriter
    processed: ProcessedTelemetryBundleSectionWriter


class MetoceanBundleSectionWriter(Protocol):
    """
    Write primitive for a bundle's ``metocean`` section.

    Write-once — it raises if the target node already exists.
    """

    def write(self, provider: str, variable: str, frame: pd.DataFrame) -> None:
        """Write one metocean table."""
        ...


class DeploymentBundleWriter(Protocol):
    """Write interface for a deployment bundle."""

    def write_header(self, value: DeploymentBundleHeader) -> None:
        """Write the root ``bundle`` table."""
        ...

    deployment: DeploymentBundleSectionWriter
    platform: PlatformBundleSectionWriter
    vessel: VesselBundleSectionWriter
    telemetry: TelemetryBundleSectionWriter
    metocean: MetoceanBundleSectionWriter
