"""Validators for the Benthloc telemetry ingestion document builder.

Structural errors (a bad config, or a config that does not match the bundle)
are raised here, before any samples are read. Softer, per-series issues
discovered while building are reported through the diagnostics callbacks by
the builder instead.
"""

from benthloc.models import MeasurementPayload

from .telemetry_types import (
    TelemetryIngestionConfig,
    WarningCallback,
)


def validate_config_series_identities(config: TelemetryIngestionConfig) -> None:
    """
    Assert every `SeriesEntry` names a configured sensor and that series
    identities are unique.

    Arguments
    ---------
    config: Parsed builder config.

    Raises
    ------
    ValueError: If a `SeriesEntry.sensor_key` matches no `SensorEntry`, or
        two series resolve to the same `(sensor_key, series_key)`.
    """
    sensor_keys: set[str] = {entry.sensor_key for entry in config.sensors}

    unknown: list[str] = sorted(
        {
            series.sensor_key
            for series in config.series
            if series.sensor_key not in sensor_keys
        }
    )
    if unknown:
        raise ValueError(
            f"series reference sensor keys with no SensorEntry: {unknown}"
        )

    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for series in config.series:
        identity = (series.sensor_key, series.series_key)
        if identity in seen:
            duplicates.add(identity)
        seen.add(identity)
    if duplicates:
        raise ValueError(
            f"duplicate (sensor_key, series_key) series identities: "
            f"{sorted(duplicates)}"
        )


def validate_config_against_bundle(
    config: TelemetryIngestionConfig,
    bundle_sensor_keys: set[str],
) -> None:
    """
    Assert every configured sensor names a sensor present in the bundle.

    Arguments
    ---------
    config: Parsed builder config.
    bundle_sensor_keys: Sensor keys the bundle holds a
        `platform/sensors/<sensor_key>/...` frame for.

    Raises
    ------
    ValueError: If a `SensorEntry.sensor_key` names no bundle sensor.
    """
    missing: list[str] = sorted(
        {
            entry.sensor_key
            for entry in config.sensors
            if entry.sensor_key not in bundle_sensor_keys
        }
    )
    if missing:
        raise ValueError(
            f"config sensor keys absent from the bundle: {missing} "
            f"(bundle holds {sorted(bundle_sensor_keys)})"
        )


def check_columns_against_schema(
    series: TelemetryIngestionConfig.SeriesEntry,
    on_warning: WarningCallback,
    payload_type: type[MeasurementPayload] | None,
) -> None:
    """
    Warn if a series' `columns` map does not line up with the measurement
    type it names.

    This is advisory only: Benthloc is the authority that validates each
    payload against its measurement schema. A `payload_schema_name` outside
    Benthloc's vocabulary is warned about but not treated as an error. The
    payload model's fields are read once per series here, never per row.

    Arguments
    ---------
    series: Series to check.
    on_warning: Callback invoked with `(topic, message)` per issue found.
    payload_type: The Benthloc payload model, or `None` if the series' key is
        outside Benthloc's vocabulary.
    """
    topic: str = f"{series.sensor_key}/{series.series_key}"

    if payload_type is None:
        on_warning(
            topic,
            f"payload_schema_name {series.payload_schema_name!r} is not in "
            f"the known measurement vocabulary",
        )
        return

    fields: set[str] = set(payload_type.model_fields)
    required_fields: set[str] = {
        name
        for name, field in payload_type.model_fields.items()
        if field.is_required()
    }
    target_fields: set[str] = set(series.columns.values())

    unknown: list[str] = sorted(target_fields - fields)
    if unknown:
        on_warning(
            topic,
            f"columns map fields not in measurement type "
            f"{series.payload_schema_name!r}: {unknown}",
        )

    missing_required: list[str] = sorted(required_fields - target_fields)
    if missing_required:
        on_warning(
            topic,
            f"columns map does not cover required fields of "
            f"{series.payload_schema_name!r}: {missing_required}",
        )
