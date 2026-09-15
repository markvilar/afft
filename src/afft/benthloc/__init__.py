"""Package for Benthloc ingestion document builders -- format knowledge for
Benthloc's file formats, separate from `afft.tasks` and `afft.cli`."""

from .common_types import (
    ResolvedIdentity as ResolvedIdentity,
    resolve_identity as resolve_identity,
)
from .common_validators import (
    check_crs_is_wgs84 as check_crs_is_wgs84,
    check_geometry_is_point_z as check_geometry_is_point_z,
    check_positions_valid_geodetic as check_positions_valid_geodetic,
    check_timestamps_monotonically_increasing as check_timestamps_monotonically_increasing,
    check_timestamps_tz_aware_utc as check_timestamps_tz_aware_utc,
)
from .trajectory_types import (
    BuildTrajectoryIngestionDocumentCommand as BuildTrajectoryIngestionDocumentCommand,
    BuildTrajectoryIngestionDocumentResult as BuildTrajectoryIngestionDocumentResult,
)
from .trajectory_validators import (
    validate_trajectory_geoframe as validate_trajectory_geoframe,
)
from .trajectory_builder import (
    run_build_trajectory_ingestion_document as run_build_trajectory_ingestion_document,
    validate_build_trajectory_ingestion_document_input as validate_build_trajectory_ingestion_document_input,
)
from benthloc.ingestion import (
    TelemetrySampleEntry as TelemetrySampleEntry,
    TelemetrySensorEntry as TelemetrySensorEntry,
    TelemetrySensorExtrinsicsEntry as TelemetrySensorExtrinsicsEntry,
    TelemetrySeriesEntry as TelemetrySeriesEntry,
)
from .telemetry_types import (
    BuildTelemetryIngestionDocumentCommand as BuildTelemetryIngestionDocumentCommand,
    BuildTelemetryIngestionDocumentResult as BuildTelemetryIngestionDocumentResult,
    TelemetryIngestionConfig as TelemetryIngestionConfig,
    TelemetryIngestionDiagnostics as TelemetryIngestionDiagnostics,
    TelemetryIngestionError as TelemetryIngestionError,
    TelemetryIngestionWarning as TelemetryIngestionWarning,
)
from .telemetry_validators import (
    check_columns_against_schema as check_columns_against_schema,
    validate_config_against_bundle as validate_config_against_bundle,
    validate_config_series_identities as validate_config_series_identities,
)
from .telemetry_builder import (
    build_payload as build_payload,
    build_sensor_entries as build_sensor_entries,
    build_series_entry as build_series_entry,
    resolve_payload_type as resolve_payload_type,
    euler_zyx_to_matrix as euler_zyx_to_matrix,
    read_build_telemetry_ingestion_document_config as read_build_telemetry_ingestion_document_config,
    run_build_telemetry_ingestion_document as run_build_telemetry_ingestion_document,
    validate_build_telemetry_ingestion_document_input as validate_build_telemetry_ingestion_document_input,
)

__all__ = []
