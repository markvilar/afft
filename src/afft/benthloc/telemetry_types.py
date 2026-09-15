"""Data types for the Benthloc telemetry ingestion document builder.

The output document DTOs (`TelemetryIngestionDocument`, `Telemetry*Entry`) and
the measurement vocabulary are imported from Benthloc (`benthloc.ingestion` /
`benthloc.models`); Benthloc is the single source of truth for both. Only
AFFT's own build-time concerns live here: the parsed builder config, the
diagnostics collector, and the command/result models.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

type WarningCallback = Callable[[str, str], None]
type ErrorCallback = Callable[[str, str], None]


class TelemetryIngestionWarning(BaseModel):
    """
    A non-fatal issue encountered during the build.

    Attributes
    ----------
    topic: Series, sensor, or frame key the warning concerns.
    message: Human-readable description of the issue.
    """

    model_config = ConfigDict(frozen=True)

    topic: str
    message: str


class TelemetryIngestionError(BaseModel):
    """
    An error collected during the build; a non-empty set fails the run.

    Attributes
    ----------
    topic: Series, sensor, or frame key the error concerns.
    message: Human-readable description of the issue.
    """

    model_config = ConfigDict(frozen=True)

    topic: str
    message: str


class TelemetryIngestionDiagnostics(BaseModel):
    """
    Accumulates issues encountered during the build for deferred reporting.

    Its `warning` / `error` methods satisfy the `WarningCallback` /
    `ErrorCallback` aliases, so they pass straight into the building
    functions.

    Attributes
    ----------
    warnings: Non-fatal issues, per topic.
    errors: Errors collected during building; a non-empty list fails the run
        after building completes (never on a dry run).
    dropped_sample_count: Samples dropped for a non-finite required payload
        value, across all series.
    """

    warnings: list[TelemetryIngestionWarning] = Field(default_factory=list)
    errors: list[TelemetryIngestionError] = Field(default_factory=list)
    dropped_sample_count: int = 0

    def warning(self, topic: str, message: str) -> None:
        """Append a warning for a topic."""
        self.warnings.append(
            TelemetryIngestionWarning(topic=topic, message=message)
        )

    def error(self, topic: str, message: str) -> None:
        """Append an error for a topic."""
        self.errors.append(
            TelemetryIngestionError(topic=topic, message=message)
        )

    def drop_samples(self, count: int) -> None:
        """Record dropped samples."""
        self.dropped_sample_count += count


class TelemetryIngestionConfig(BaseModel):
    """
    Parsed `[afft.benthloc.build_telemetry_ingestion_document]` config.

    Attributes
    ----------
    sensors: Per-sensor config for the sensors emitted in the document.
    series: Series definitions; several may share a frame_key.
    """

    model_config = ConfigDict(frozen=True)

    class SensorEntry(BaseModel):
        """
        Per-sensor config for one emitted `telemetry_sensors` entry.

        Only the fields the bundle does not carry appear here; sensor
        identity (label/type/vendor/model) and extrinsics are read from
        `platform/sensors/<sensor_key>/...`, and platform/deployment keys
        from the bundle identity frames.

        Attributes
        ----------
        sensor_key: Bundle sensor key this entry configures; must name a
            `platform/sensors/<sensor_key>/...` sensor and be referenced by
            at least one SeriesEntry.
        metadata: Arbitrary key-value metadata for the emitted entry.
        """

        model_config = ConfigDict(frozen=True)

        sensor_key: str
        metadata: dict[str, Any] = Field(default_factory=dict)

    class SeriesEntry(BaseModel):
        """
        One output series: a column subset of a bundle frame.

        Attributes
        ----------
        frame_key: Bundle frame key to read (e.g. a `telemetry/...` key).
        sensor_key: Bundle sensor key that owns this series; the emitted
            series resolves to the `telemetry_sensors` entry for it, and it
            must match a SensorEntry.
        series_key: Stream identity discriminator asserted in the output;
            `(sensor_key, series_key)` must be unique across `series`.
        payload_schema_name: Registered Benthloc `measurement_key` the
            samples validate against.
        columns: Frame column name -> measurement payload field name;
            selects and renames the subset that becomes each sample's
            payload.
        """

        model_config = ConfigDict(frozen=True)

        frame_key: str
        sensor_key: str
        series_key: str
        payload_schema_name: str
        columns: dict[str, str]

    sensors: list[SensorEntry] = Field(default_factory=list)
    series: list[SeriesEntry] = Field(default_factory=list)


class BuildTelemetryIngestionDocumentCommand(BaseModel):
    """
    Command for the telemetry ingestion document builder.

    Attributes
    ----------
    bundle_file: Path to the built deployment bundle to read from.
    config_file: Path to the shared task config TOML file
        (`config/default.toml`) holding the
        `[afft.benthloc.build_telemetry_ingestion_document]` section.
    output_file: Path to write the Benthloc telemetry ingestion document to.
    overwrite: Overwrite `output_file` if it already exists.
    dry_run: Validate and report the keys the document asserts without
        writing it.
    verbose: Log accumulated diagnostics after the run completes.
    """

    model_config = ConfigDict(frozen=True)

    bundle_file: Path
    config_file: Path
    output_file: Path
    overwrite: bool = False
    dry_run: bool = False
    verbose: bool = False


class BuildTelemetryIngestionDocumentResult(BaseModel):
    """
    Attributes
    ----------
    output_file: Path the document was (or would be) written to.
    platform_key: Platform key the document asserts.
    deployment_key: Deployment key the document asserts.
    sensor_count: Number of `telemetry_sensors` entries.
    series_count: Number of `telemetry_series` entries.
    sample_count: Total samples across every series.
    dropped_sample_count: Samples dropped for a non-finite required value.
    written: Whether the file was actually written (`False` for `dry_run`).
    diagnostics: Warnings and errors accumulated during the run.
    """

    model_config = ConfigDict(frozen=True)

    output_file: Path
    platform_key: str
    deployment_key: str
    sensor_count: int
    series_count: int
    sample_count: int
    dropped_sample_count: int
    written: bool
    diagnostics: TelemetryIngestionDiagnostics
