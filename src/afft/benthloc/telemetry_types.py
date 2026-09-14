"""Data types for the Benthloc telemetry ingestion document builder.

The output entry models (`Telemetry*Entry`) mirror the schema of
`src/benthloc/tasks/telemetry_ingestion/types.py` in `markvilar/benthloc`;
they model an external contract rather than an AFFT domain concept. The
measurement vocabulary (`MEASUREMENT_SCHEMAS`) is the revised set from
benthloc#640, carried here only to drive build-time warnings and the
required/optional distinction that decides how a non-finite payload value is
handled; Benthloc remains the authority that validates each payload.
"""

from collections.abc import Callable
from datetime import datetime
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


class MeasurementSchema(BaseModel):
    """
    The stored field set of a Benthloc measurement type.

    Derived properties (computed on Benthloc's side) are never listed here,
    since a `columns` map never targets them.

    Attributes
    ----------
    required_fields: Fields that must carry a finite value; a non-finite
        value in one drops the sample.
    optional_fields: Fields omitted from the payload when non-finite.
    integer_fields: Fields emitted as integers rather than floats.
    """

    model_config = ConfigDict(frozen=True)

    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    integer_fields: tuple[str, ...] = ()

    def fields(self) -> set[str]:
        """Every stored field, required or optional."""
        return set(self.required_fields) | set(self.optional_fields)


# The revised measurement vocabulary from benthloc#640. The concrete
# per-series choices are made in the configuration sub-issue; this registry
# drives only build-time warnings and the required/optional distinction.
MEASUREMENT_SCHEMAS: dict[str, MeasurementSchema] = {
    "linear_velocity": MeasurementSchema(
        required_fields=("velx", "vely", "velz"),
        optional_fields=("velx_std", "vely_std", "velz_std"),
    ),
    "attitude": MeasurementSchema(
        required_fields=("roll", "pitch", "yaw"),
        optional_fields=("roll_std", "pitch_std", "yaw_std"),
    ),
    "dvl_beam_ranges": MeasurementSchema(
        required_fields=("range_01", "range_02", "range_03", "range_04"),
    ),
    "teledyne_dvl_ensemble": MeasurementSchema(
        required_fields=(
            "altitude",
            "range_01",
            "range_02",
            "range_03",
            "range_04",
            "heading",
            "pitch",
            "roll",
            "velocity_x",
            "velocity_y",
            "velocity_z",
            "dmg_x",
            "dmg_y",
            "dmg_z",
            "course_over_ground",
            "speed_over_ground",
            "true_heading",
            "gimbal_pitch",
            "sound_velocity",
            "bottom_track_status",
        ),
        integer_fields=("bottom_track_status",),
    ),
    "acoustic_transponder_fix": MeasurementSchema(
        required_fields=("latitude", "longitude", "height"),
    ),
    "acoustic_transceiver_fix": MeasurementSchema(
        required_fields=("latitude", "longitude"),
        optional_fields=("height",),
    ),
    "acoustic_link_fix": MeasurementSchema(
        required_fields=(
            "target_latitude",
            "target_longitude",
            "target_height",
            "ship_latitude",
            "ship_longitude",
        ),
        optional_fields=("ship_height",),
    ),
    "acoustic_link_ensemble": MeasurementSchema(
        required_fields=(
            "target_latitude",
            "target_longitude",
            "target_height",
            "ship_latitude",
            "ship_longitude",
            "target_x_sensor",
            "target_y_sensor",
            "target_z_sensor",
        ),
    ),
    "pressure_depth": MeasurementSchema(
        required_fields=("depth",),
        optional_fields=("depth_std", "sea_level"),
    ),
}


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


class TelemetrySensorExtrinsicsEntry(BaseModel):
    """
    A sensor's mounting pose, as one Benthloc `extrinsics` entry.

    Attributes
    ----------
    source: Identity within the sensor's extrinsics set; a constant
        `"unknown"`, since AFFT carries no pose provenance.
    is_default: Whether this is the sensor's default pose.
    location: Sensor origin in the body frame, `[x, y, z]` in metres.
    rotation: Row-major 3x3 matrix mapping sensor-frame to body-frame.
    description: Optional human-readable description.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    is_default: bool
    location: list[float]
    rotation: list[list[float]]
    description: str | None = None


class TelemetrySensorEntry(BaseModel):
    """
    A `PlatformSensor` with its mounting extrinsics, one Benthloc
    `telemetry_sensors` entry.

    Attributes
    ----------
    platform_key: Strict reference to an existing Platform.
    deployment_key: Strict reference to an existing Deployment.
    sensor_key: Identity `(platform_deployment, sensor_key)`.
    sensor_label: Display label.
    sensor_type: Sensor type.
    sensor_vendor: Manufacturer; empty where unrecorded.
    sensor_model: Product name; empty where unrecorded.
    description: Optional human-readable description.
    metadata: Arbitrary key-value metadata.
    extrinsics: Mounting poses; empty when the sensor has no surveyed pose.
    """

    model_config = ConfigDict(frozen=True)

    platform_key: str
    deployment_key: str
    sensor_key: str
    sensor_label: str
    sensor_type: str
    sensor_vendor: str
    sensor_model: str
    description: str | None
    metadata: dict[str, Any]
    extrinsics: list[TelemetrySensorExtrinsicsEntry]


class TelemetrySampleEntry(BaseModel):
    """
    One timestamped sample of a telemetry series.

    Attributes
    ----------
    timestamp: Sample timestamp, tz-aware UTC.
    payload: Exact stored fields of the series' measurement type.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    payload: dict[str, Any]


class TelemetrySeriesEntry(BaseModel):
    """
    One `TelemetrySeries` collection, one Benthloc `telemetry_series` entry.

    Attributes
    ----------
    platform_key: Strict reference to an existing Platform.
    deployment_key: Strict reference to an existing Deployment.
    sensor_key: Strict reference to a `telemetry_sensors` entry.
    series_key: With `sensor_key`, the TelemetrySeries identity.
    payload_schema_name: A registered Benthloc `measurement_key`.
    samples: The series' timestamped samples.
    """

    model_config = ConfigDict(frozen=True)

    platform_key: str
    deployment_key: str
    sensor_key: str
    series_key: str
    payload_schema_name: str
    samples: list[TelemetrySampleEntry]


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
