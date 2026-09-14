"""Builder for the Benthloc telemetry ingestion document: reads a built
deployment bundle and writes the normalized JSON document Benthloc's
`telemetry_ingestion` task reads.

The document is written incrementally -- the `telemetry_sensors` section
first (ingestion ordering requires it), then the `telemetry_series` entries
one at a time -- so a full deployment's millions of samples are never held
as a single in-memory document.
"""

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import afft.io as io

from afft.deployment import (
    DeploymentBundleReader,
    DeploymentIdentity,
    PlatformIdentity,
    SensorExtrinsics,
    SensorIdentity,
    open_deployment_bundle_reader,
)
from afft.utils.log import logger

from .common_validators import check_timestamps_tz_aware_utc
from .telemetry_types import (
    MEASUREMENT_SCHEMAS,
    BuildTelemetryIngestionDocumentCommand,
    BuildTelemetryIngestionDocumentResult,
    MeasurementSchema,
    TelemetryIngestionConfig,
    TelemetryIngestionDiagnostics,
    TelemetrySampleEntry,
    TelemetrySensorEntry,
    TelemetrySensorExtrinsicsEntry,
    TelemetrySeriesEntry,
    WarningCallback,
)
from .telemetry_validators import (
    check_columns_against_schema,
    validate_config_against_bundle,
    validate_config_series_identities,
)

_PLATFORM_IDENTITY_KEY: str = "platform/identity"
_DEPLOYMENT_IDENTITY_KEY: str = "deployment/identity"
_PLATFORM_SENSORS_PREFIX: str = "platform/sensors/"
_TIMESTAMP_COLUMN: str = "timestamp"
_EXTRINSICS_SOURCE: str = "unknown"


def read_build_telemetry_ingestion_document_config(
    config_file: Path,
) -> TelemetryIngestionConfig:
    """
    Read the builder's config section from the shared task config file.

    A missing section parses to an empty config (no sensors, no series),
    matching the minimal stub in `config/default.toml`.

    Arguments
    ---------
    config_file: Path to the shared task config TOML file.

    Returns
    -------
    The builder's parsed config.
    """
    raw: dict[str, Any] = io.read_config(config_file)
    section: dict[str, Any] = (
        raw.get("afft", {})
        .get("benthloc", {})
        .get("build_telemetry_ingestion_document", {})
    )
    return TelemetryIngestionConfig(**section)


def validate_build_telemetry_ingestion_document_input(
    command: BuildTelemetryIngestionDocumentCommand,
    config: TelemetryIngestionConfig,
) -> None:
    """
    Validate the task's inputs before any expensive work runs.

    Bundle-dependent config checks (that every configured sensor names a
    bundle sensor) happen once the reader is open; see
    `validate_config_against_bundle`.

    Arguments
    ---------
    command: Task command.
    config: Parsed builder config.

    Raises
    ------
    FileNotFoundError: If the bundle file or the output directory does not
        exist.
    FileExistsError: If the output file already exists, `overwrite` is not
        set, and the run is not a `dry_run`.
    ValueError: If a `SeriesEntry.sensor_key` matches no `SensorEntry`, or
        two series share a `(sensor_key, series_key)` identity.
    """
    if not command.bundle_file.is_file():
        raise FileNotFoundError(
            f"bundle file does not exist: {command.bundle_file}"
        )

    if not command.output_file.parent.is_dir():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    if (
        not command.dry_run
        and command.output_file.exists()
        and not command.overwrite
    ):
        raise FileExistsError(
            f"output file already exists: {command.output_file}"
        )

    validate_config_series_identities(config)


def _bundle_sensor_keys(reader: DeploymentBundleReader) -> set[str]:
    """Collect the sensor keys the bundle holds a
    `platform/sensors/<sensor_key>/...` frame for."""
    keys: set[str] = set()
    for frame_key in reader.list_frames():
        if frame_key.startswith(_PLATFORM_SENSORS_PREFIX):
            rest: str = frame_key[len(_PLATFORM_SENSORS_PREFIX) :]
            keys.add(rest.split("/", 1)[0])
    return keys


def _read_identity_keys(reader: DeploymentBundleReader) -> tuple[str, str]:
    """Read the Benthloc-compatible platform and deployment keys straight
    from the bundle's identity frames (populated by #314)."""
    platform_identity = PlatformIdentity(
        **reader.read_frame(_PLATFORM_IDENTITY_KEY).iloc[0].to_dict()
    )
    deployment_identity = DeploymentIdentity(
        **reader.read_frame(_DEPLOYMENT_IDENTITY_KEY).iloc[0].to_dict()
    )
    return platform_identity.platform_key, deployment_identity.deployment_key


def euler_zyx_to_matrix(
    rotx: float, roty: float, rotz: float
) -> list[list[float]]:
    """
    Convert Z-Y-X intrinsic Euler angles to a row-major rotation matrix.

    The composition is `rotz` then `roty` then `rotx` (intrinsic), i.e.
    `R = Rz @ Ry @ Rx`. AFFT's `SensorExtrinsics.rotation` maps sensor-frame
    to body-frame and is emitted unchanged, which is the convention Benthloc
    consumes.

    Arguments
    ---------
    rotx: Roll angle in radians.
    roty: Pitch angle in radians.
    rotz: Yaw angle in radians.

    Returns
    -------
    The row-major 3x3 rotation matrix as a list of rows.
    """
    cx, sx = np.cos(rotx), np.sin(rotx)
    cy, sy = np.cos(roty), np.sin(roty)
    cz, sz = np.cos(rotz), np.sin(rotz)
    rotation_x = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    rotation_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rotation_z = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    rotation = rotation_z @ rotation_y @ rotation_x
    return [[float(value) for value in row] for row in rotation]


def _build_extrinsics_entry(
    extrinsics: SensorExtrinsics,
) -> TelemetrySensorExtrinsicsEntry:
    """Build the single default extrinsics entry for a sensor's pose."""
    return TelemetrySensorExtrinsicsEntry(
        source=_EXTRINSICS_SOURCE,
        is_default=True,
        location=[extrinsics.locx, extrinsics.locy, extrinsics.locz],
        rotation=euler_zyx_to_matrix(
            extrinsics.rotx, extrinsics.roty, extrinsics.rotz
        ),
        description=None,
    )


def build_sensor_entries(
    reader: DeploymentBundleReader,
    config: TelemetryIngestionConfig,
    platform_key: str,
    deployment_key: str,
    on_warning: WarningCallback,
) -> list[TelemetrySensorEntry]:
    """
    Build one `telemetry_sensors` entry per configured sensor.

    Identity and extrinsics are read from `platform/sensors/<sensor_key>/...`;
    a sensor missing either is warned about and emitted with empty identity
    fields or no extrinsics.

    Arguments
    ---------
    reader: Open bundle reader.
    config: Parsed builder config.
    platform_key: Platform key read from the bundle identity frame.
    deployment_key: Deployment key read from the bundle identity frame.
    on_warning: Callback invoked with `(topic, message)` per issue found.

    Returns
    -------
    The sensor entries, in config order.
    """
    entries: list[TelemetrySensorEntry] = []
    for sensor in config.sensors:
        identity_key: str = (
            f"{_PLATFORM_SENSORS_PREFIX}{sensor.sensor_key}/identity"
        )
        extrinsics_key: str = (
            f"{_PLATFORM_SENSORS_PREFIX}{sensor.sensor_key}/extrinsics"
        )

        if reader.has_frame(identity_key):
            identity = SensorIdentity(
                **reader.read_frame(identity_key).iloc[0].to_dict()
            )
            label, sensor_type = identity.label, identity.type
            vendor, model = identity.vendor, identity.product
        else:
            on_warning(sensor.sensor_key, "sensor has no identity frame")
            label = sensor_type = vendor = model = ""

        extrinsics_entries: list[TelemetrySensorExtrinsicsEntry] = []
        if reader.has_frame(extrinsics_key):
            extrinsics = SensorExtrinsics(
                **reader.read_frame(extrinsics_key).iloc[0].to_dict()
            )
            extrinsics_entries.append(_build_extrinsics_entry(extrinsics))
        else:
            on_warning(sensor.sensor_key, "sensor has no extrinsics frame")

        entries.append(
            TelemetrySensorEntry(
                platform_key=platform_key,
                deployment_key=deployment_key,
                sensor_key=sensor.sensor_key,
                sensor_label=label,
                sensor_type=sensor_type,
                sensor_vendor=vendor,
                sensor_model=model,
                description=None,
                metadata=sensor.metadata,
                extrinsics=extrinsics_entries,
            )
        )
    return entries


def _is_present(value: Any) -> bool:
    """Return whether a value is a usable (finite, non-null) payload value."""
    if value is None or (np.isscalar(value) and pd.isna(value)):
        return False
    if isinstance(value, (int, float, np.integer, np.floating)) and not (
        isinstance(value, bool)
    ):
        return bool(np.isfinite(value))
    return True


def _to_native(value: Any, is_integer: bool) -> Any:
    """Convert a frame value to a JSON-serializable native Python scalar."""
    if is_integer:
        return int(value)
    if isinstance(value, (np.integer, np.floating, int, float)) and not (
        isinstance(value, bool)
    ):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def build_payload(
    row: Mapping[str, Any],
    columns: Mapping[str, str],
    schema: MeasurementSchema | None,
) -> dict[str, Any] | None:
    """
    Select and rename a frame row into a measurement payload.

    A non-finite value in a required field drops the sample (returns
    `None`); in an optional field it is omitted. When the schema is unknown,
    every mapped field is treated as required.

    Arguments
    ---------
    row: Frame row, keyed by source column name.
    columns: Source column name -> measurement payload field name.
    schema: The measurement type, or `None` if outside the known
        vocabulary.

    Returns
    -------
    The payload, or `None` if the sample must be dropped.
    """
    required: set[str] = (
        set(schema.required_fields) if schema is not None else set()
    )
    integer_fields: set[str] = (
        set(schema.integer_fields) if schema is not None else set()
    )

    payload: dict[str, Any] = {}
    for source_column, target_field in columns.items():
        value: Any = row[source_column]
        if not _is_present(value):
            if schema is None or target_field in required:
                return None
            continue
        payload[target_field] = _to_native(
            value, target_field in integer_fields
        )
    return payload


def build_series_entry(
    reader: DeploymentBundleReader,
    series: TelemetryIngestionConfig.SeriesEntry,
    platform_key: str,
    deployment_key: str,
    diagnostics: TelemetryIngestionDiagnostics,
    schemas: Mapping[str, MeasurementSchema] = MEASUREMENT_SCHEMAS,
) -> TelemetrySeriesEntry | None:
    """
    Build one `telemetry_series` entry from its configured bundle frame.

    Returns `None` (and reports a warning or error) when the series cannot
    be built: an absent frame is a warning, a missing column or a
    non-tz-aware timestamp column is an error.

    Arguments
    ---------
    reader: Open bundle reader.
    series: Series definition.
    platform_key: Platform key the entry asserts.
    deployment_key: Deployment key the entry asserts.
    diagnostics: Collector for warnings, errors, and drop counts.
    schemas: Known measurement vocabulary.

    Returns
    -------
    The series entry, or `None` if the series was skipped.
    """
    topic: str = f"{series.sensor_key}/{series.series_key}"

    if not reader.has_frame(series.frame_key):
        diagnostics.warning(
            topic, f"frame {series.frame_key!r} is absent from the bundle"
        )
        return None

    frame: pd.DataFrame = reader.read_frame(series.frame_key)

    needed: list[str] = [_TIMESTAMP_COLUMN, *series.columns.keys()]
    missing: list[str] = sorted(set(needed) - set(frame.columns))
    if missing:
        diagnostics.error(
            topic, f"frame {series.frame_key!r} is missing columns: {missing}"
        )
        return None

    try:
        check_timestamps_tz_aware_utc(frame[_TIMESTAMP_COLUMN])
    except ValueError as error:
        diagnostics.error(topic, str(error))
        return None

    check_columns_against_schema(series, diagnostics.warning, schemas)
    schema: MeasurementSchema | None = schemas.get(series.payload_schema_name)

    subframe: pd.DataFrame = frame.loc[:, needed].sort_values(_TIMESTAMP_COLUMN)
    source_columns: list[str] = list(series.columns.keys())

    samples: list[TelemetrySampleEntry] = []
    dropped: int = 0
    for record in subframe.itertuples(index=False, name=None):
        timestamp: pd.Timestamp = record[0]
        row: dict[str, Any] = dict(zip(source_columns, record[1:]))
        payload: dict[str, Any] | None = build_payload(
            row, series.columns, schema
        )
        if payload is None:
            dropped += 1
            continue
        samples.append(
            TelemetrySampleEntry(
                timestamp=timestamp.to_pydatetime(), payload=payload
            )
        )

    if dropped:
        diagnostics.drop_samples(dropped)
        diagnostics.warning(
            topic,
            f"dropped {dropped} sample(s) with a non-finite required value",
        )

    return TelemetrySeriesEntry(
        platform_key=platform_key,
        deployment_key=deployment_key,
        sensor_key=series.sensor_key,
        series_key=series.series_key,
        payload_schema_name=series.payload_schema_name,
        samples=samples,
    )


def _iter_series_entries(
    reader: DeploymentBundleReader,
    config: TelemetryIngestionConfig,
    platform_key: str,
    deployment_key: str,
    diagnostics: TelemetryIngestionDiagnostics,
) -> Iterator[TelemetrySeriesEntry]:
    """Yield each built series entry, skipping series that could not be
    built. One series (with its samples) is resident at a time."""
    for series in config.series:
        entry = build_series_entry(
            reader, series, platform_key, deployment_key, diagnostics
        )
        if entry is not None:
            yield entry


def _write_document(
    output_file: Path,
    sensor_entries: list[TelemetrySensorEntry],
    series_entries: Iterator[TelemetrySeriesEntry],
) -> tuple[int, int]:
    """Stream the document to `output_file`, writing `telemetry_sensors`
    first and then each `telemetry_series` entry one at a time. Returns the
    series and sample counts written."""
    series_count: int = 0
    sample_count: int = 0
    with output_file.open("w", encoding="utf-8") as file:
        file.write('{"telemetry_sensors": ')
        json.dump(
            [entry.model_dump(mode="json") for entry in sensor_entries], file
        )
        file.write(', "telemetry_series": [')
        for entry in series_entries:
            if series_count:
                file.write(", ")
            json.dump(entry.model_dump(mode="json"), file)
            series_count += 1
            sample_count += len(entry.samples)
        file.write("]}")
    return series_count, sample_count


def _count_series_entries(
    series_entries: Iterator[TelemetrySeriesEntry],
) -> tuple[int, int]:
    """Consume the series entries to accumulate counts and diagnostics
    without writing (used for a dry run)."""
    series_count: int = 0
    sample_count: int = 0
    for entry in series_entries:
        series_count += 1
        sample_count += len(entry.samples)
    return series_count, sample_count


def run_build_telemetry_ingestion_document(
    command: BuildTelemetryIngestionDocumentCommand,
    config: TelemetryIngestionConfig,
) -> BuildTelemetryIngestionDocumentResult:
    """
    Build a Benthloc telemetry ingestion document from a built deployment
    bundle.

    Arguments
    ---------
    command: Task command.
    config: Parsed builder config; the CLI action reads it from
        `command.config_file` and passes it in, keeping this runner pure.

    Returns
    -------
    The run's result, naming the asserted keys, counts, and diagnostics.

    Raises
    ------
    FileNotFoundError: If the bundle file or the output directory does not
        exist.
    FileExistsError: If the output file already exists, `overwrite` is not
        set, and the run is not a `dry_run`.
    ValueError: If the config is inconsistent (bad series identities, or a
        configured sensor absent from the bundle), or one or more series
        failed to build on a non-dry run.
    """
    validate_build_telemetry_ingestion_document_input(command, config)

    diagnostics = TelemetryIngestionDiagnostics()

    reader: DeploymentBundleReader
    with open_deployment_bundle_reader(command.bundle_file) as reader:
        validate_config_against_bundle(config, _bundle_sensor_keys(reader))
        platform_key, deployment_key = _read_identity_keys(reader)

        sensor_entries: list[TelemetrySensorEntry] = build_sensor_entries(
            reader, config, platform_key, deployment_key, diagnostics.warning
        )
        series_entries: Iterator[TelemetrySeriesEntry] = _iter_series_entries(
            reader, config, platform_key, deployment_key, diagnostics
        )

        if command.dry_run:
            series_count, sample_count = _count_series_entries(series_entries)
        else:
            series_count, sample_count = _write_document(
                command.output_file, sensor_entries, series_entries
            )

    logger.info("-------------------------------------")
    logger.info("Build Telemetry Ingestion Document")
    logger.info(f"  bundle file:  {command.bundle_file}")
    logger.info(f"  output file:  {command.output_file}")
    logger.info(f"  platform:     {platform_key}")
    logger.info(f"  deployment:   {deployment_key}")
    logger.info(f"  sensors:      {len(sensor_entries)}")
    logger.info(f"  series:       {series_count}")
    logger.info(f"  samples:      {sample_count}")
    logger.info(f"  dropped:      {diagnostics.dropped_sample_count}")
    logger.info(f"  warnings:     {len(diagnostics.warnings)}")
    logger.info(f"  errors:       {len(diagnostics.errors)}")
    logger.info("-------------------------------------")

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.topic}: {warning.message}")
        for build_error in diagnostics.errors:
            logger.error(f"{build_error.topic}: {build_error.message}")

    if not command.dry_run:
        logger.info(
            f"wrote telemetry ingestion document to {command.output_file}"
        )
        if diagnostics.errors:
            messages: str = "; ".join(
                f"{error.topic}: {error.message}"
                for error in diagnostics.errors
            )
            raise ValueError(
                f"telemetry ingestion build had errors: {messages}"
            )

    return BuildTelemetryIngestionDocumentResult(
        output_file=command.output_file,
        platform_key=platform_key,
        deployment_key=deployment_key,
        sensor_count=len(sensor_entries),
        series_count=series_count,
        sample_count=sample_count,
        dropped_sample_count=diagnostics.dropped_sample_count,
        written=not command.dry_run,
        diagnostics=diagnostics,
    )
