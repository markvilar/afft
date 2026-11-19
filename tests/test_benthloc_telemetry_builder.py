"""Tests for the Benthloc telemetry ingestion document builder."""

import json
import math

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from afft.deployment import open_deployment_bundle

from afft.benthloc import (
    BuildTelemetryIngestionDocumentCommand,
    BuildTelemetryIngestionDocumentResult,
    TelemetryIngestionConfig,
    TelemetryIngestionDiagnostics,
    build_payload,
    euler_zyx_to_matrix,
    read_build_telemetry_ingestion_document_config,
    resolve_payload_type,
    run_build_telemetry_ingestion_document,
)


def _telemetry_frame(
    timestamps: list[str],
    velx: list[float | None] | None = None,
) -> pd.DataFrame:
    count = len(timestamps)
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps, utc=True),
            "velx": velx
            if velx is not None
            else [float(index) for index in range(count)],
            "vely": [0.1] * count,
            "velz": [0.2] * count,
        }
    )


def _bundle(
    path: Path,
    frame: pd.DataFrame | None = None,
    with_identity: bool = True,
    with_sensor_identity: bool = True,
    with_sensor_extrinsics: bool = True,
) -> Path:
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "telemetry/dvl/linear_velocity",
            frame
            if frame is not None
            else _telemetry_frame(
                ["2024-01-01T00:00:00Z", "2024-01-01T00:00:01Z"]
            ),
        )
        if with_identity:
            bundle.write_frame(
                "platform/identity",
                pd.DataFrame(
                    [
                        {
                            "platform_key": "auv_sirius",
                            "platform_label": "AUV Sirius",
                            "platform_class": "SEABED",
                            "platform_operator": "ACFR",
                        }
                    ]
                ),
            )
            bundle.write_frame(
                "deployment/identity",
                pd.DataFrame(
                    [
                        {
                            "deployment_key": "dk_r20240101_000000",
                            "deployment_label": "r20240101_000000",
                            "deployment_start_datetime": datetime(
                                2024, 1, 1, tzinfo=timezone.utc
                            ),
                            "deployment_end_datetime": None,
                        }
                    ]
                ),
            )
        if with_sensor_identity:
            bundle.write_frame(
                "platform/sensors/dvl_teledyne/identity",
                pd.DataFrame(
                    [
                        {
                            "label": "DVL",
                            "vendor": "Teledyne RDI",
                            "product": "Work Horse Navigator",
                            "type": "dvl",
                        }
                    ]
                ),
            )
        if with_sensor_extrinsics:
            bundle.write_frame(
                "platform/sensors/dvl_teledyne/extrinsics",
                pd.DataFrame(
                    [
                        {
                            "locx": 1.0,
                            "locy": 2.0,
                            "locz": 3.0,
                            "rotx": 0.0,
                            "roty": 0.0,
                            "rotz": 0.0,
                        }
                    ]
                ),
            )
    return path


def _config(**overrides: Any) -> TelemetryIngestionConfig:
    arguments: dict[str, Any] = {
        "sensors": [{"sensor_key": "dvl_teledyne", "metadata": {"note": "x"}}],
        "series": [
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "dvl_teledyne",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {
                    "velx": "velocity_x",
                    "vely": "velocity_y",
                    "velz": "velocity_z",
                },
            }
        ],
    }
    arguments.update(overrides)
    return TelemetryIngestionConfig(**arguments)


def _command(
    tmp_path: Path, **overrides: Any
) -> BuildTelemetryIngestionDocumentCommand:
    arguments: dict[str, Any] = {
        "bundle_file": overrides.pop("bundle_file", None)
        or _bundle(tmp_path / "bundle.gpkg"),
        "config_file": tmp_path / "config.toml",
        "output_file": tmp_path / "telemetry.json",
    }
    arguments.update(overrides)
    return BuildTelemetryIngestionDocumentCommand(**arguments)


def test_writes_a_document_matching_benthlocs_schema(tmp_path: Path) -> None:
    """A round trip writes the two-section document with one sensor and one
    series, and reports matching counts."""
    command = _command(tmp_path)
    config = _config()

    result = run_build_telemetry_ingestion_document(command, config)

    assert isinstance(result, BuildTelemetryIngestionDocumentResult)
    assert result.written
    assert result.platform_key == "auv_sirius"
    assert result.deployment_key == "dk_r20240101_000000"
    assert result.sensor_count == 1
    assert result.series_count == 1
    assert result.sample_count == 2
    assert result.dropped_sample_count == 0

    content = json.loads(command.output_file.read_text())
    assert set(content) == {"telemetry_sensors", "telemetry_series"}

    sensor = content["telemetry_sensors"][0]
    assert sensor["sensor_key"] == "dvl_teledyne"
    assert sensor["sensor_label"] == "DVL"
    assert sensor["sensor_type"] == "dvl"
    assert sensor["metadata"] == {"note": "x"}
    assert sensor["extrinsics"][0]["location"] == [1.0, 2.0, 3.0]

    series = content["telemetry_series"][0]
    assert series["sensor_key"] == "dvl_teledyne"
    assert series["series_key"] == "linear_velocity"
    assert series["payload_schema_name"] == "linear_velocity"
    assert len(series["samples"]) == 2
    assert set(series["samples"][0]["payload"]) == {
        "velocity_x",
        "velocity_y",
        "velocity_z",
    }


def test_dry_run_does_not_write_the_output_file(tmp_path: Path) -> None:
    """A dry run reports counts without touching disk."""
    command = _command(tmp_path, dry_run=True)
    config = _config()

    result = run_build_telemetry_ingestion_document(command, config)

    assert result.written is False
    assert result.series_count == 1
    assert result.sample_count == 2
    assert not command.output_file.exists()


def test_output_file_exists_and_overwrite_not_set_raises(
    tmp_path: Path,
) -> None:
    command = _command(tmp_path)
    command.output_file.write_text("existing")

    with pytest.raises(FileExistsError):
        run_build_telemetry_ingestion_document(command, _config())


def test_overwrite_allows_replacing_the_output_file(tmp_path: Path) -> None:
    command = _command(tmp_path, overwrite=True)
    command.output_file.write_text("existing")

    result = run_build_telemetry_ingestion_document(command, _config())

    assert result.written


def test_euler_identity_rotation() -> None:
    """Zero angles map to the identity matrix."""
    rotation = euler_zyx_to_matrix(0.0, 0.0, 0.0)

    assert np.allclose(rotation, np.eye(3))


def test_euler_ninety_degree_yaw() -> None:
    """A 90-degree yaw (rotz) matches the known Z rotation matrix."""
    rotation = euler_zyx_to_matrix(0.0, 0.0, math.pi / 2)

    assert np.allclose(
        rotation,
        [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
        atol=1e-12,
    )


def test_euler_composition_is_rz_ry_rx() -> None:
    """The composition equals Rz @ Ry @ Rx for arbitrary angles."""
    rotx, roty, rotz = 0.3, -0.7, 1.1
    cx, sx = math.cos(rotx), math.sin(rotx)
    cy, sy = math.cos(roty), math.sin(roty)
    cz, sz = math.cos(rotz), math.sin(rotz)
    expected = (
        np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
        @ np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
        @ np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    )

    assert np.allclose(euler_zyx_to_matrix(rotx, roty, rotz), expected)


def test_build_payload_selects_and_renames_columns() -> None:
    payload_type = resolve_payload_type("linear_velocity")

    payload = build_payload(
        {"vx": 1.0, "vy": 2.0, "vz": 3.0},
        {"vx": "velocity_x", "vy": "velocity_y", "vz": "velocity_z"},
        payload_type,
    )

    assert payload == {"velocity_x": 1.0, "velocity_y": 2.0, "velocity_z": 3.0}


def test_build_payload_drops_on_non_finite_required() -> None:
    payload_type = resolve_payload_type("linear_velocity")

    payload = build_payload(
        {"velx": float("nan"), "vely": 2.0, "velz": 3.0},
        {"velx": "velocity_x", "vely": "velocity_y", "velz": "velocity_z"},
        payload_type,
    )

    assert payload is None


def test_build_payload_omits_non_finite_optional() -> None:
    payload_type = resolve_payload_type("linear_velocity")

    payload = build_payload(
        {"velx": 1.0, "vely": 2.0, "velz": 3.0, "velx_std": float("nan")},
        {
            "velx": "velocity_x",
            "vely": "velocity_y",
            "velz": "velocity_z",
            "velx_std": "velocity_x_std",
        },
        payload_type,
    )

    assert payload == {"velocity_x": 1.0, "velocity_y": 2.0, "velocity_z": 3.0}


def test_build_payload_emits_integer_fields_as_int() -> None:
    payload_type = resolve_payload_type("teledyne_dvl_ensemble")
    row: dict[str, float] = {
        "altitude": 1.0,
        "range_01": 1.0,
        "range_02": 1.0,
        "range_03": 1.0,
        "range_04": 1.0,
        "heading": 1.0,
        "pitch": 1.0,
        "roll": 1.0,
        "velocity_x": 1.0,
        "velocity_y": 1.0,
        "velocity_z": 1.0,
        "dmg_x": 1.0,
        "dmg_y": 1.0,
        "dmg_z": 1.0,
        "course_over_ground": 1.0,
        "speed_over_ground": 1.0,
        "true_heading": 1.0,
        "gimbal_pitch": 1.0,
        "sound_velocity": 1.0,
        "bottom_track_status": 4.0,
    }
    columns = {field: field for field in row}

    payload = build_payload(row, columns, payload_type)

    assert payload is not None
    assert payload["bottom_track_status"] == 4
    assert isinstance(payload["bottom_track_status"], int)


def test_nan_row_is_dropped_and_reported(tmp_path: Path) -> None:
    """A row with a non-finite required value is dropped, counted, and
    warned about on the diagnostics."""
    frame = _telemetry_frame(
        [
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:00:01Z",
            "2024-01-01T00:00:02Z",
        ],
        velx=[1.0, float("nan"), 3.0],
    )
    bundle_file = _bundle(tmp_path / "bundle.gpkg", frame=frame)
    command = _command(tmp_path, bundle_file=bundle_file)

    result = run_build_telemetry_ingestion_document(command, _config())

    assert result.sample_count == 2
    assert result.dropped_sample_count == 1
    assert any(
        "non-finite" in warning.message
        for warning in result.diagnostics.warnings
    )


def test_one_frame_feeds_many_series(tmp_path: Path) -> None:
    """Two series may read the same frame with different column subsets."""
    config = _config(
        series=[
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "dvl_teledyne",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {
                    "velx": "velocity_x",
                    "vely": "velocity_y",
                    "velz": "velocity_z",
                },
            },
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "dvl_teledyne",
                "series_key": "velocity_x_only",
                "payload_schema_name": "custom_partial",
                "columns": {"velx": "velx"},
            },
        ]
    )
    command = _command(tmp_path)

    result = run_build_telemetry_ingestion_document(command, config)

    assert result.series_count == 2
    assert result.sample_count == 4
    content = json.loads(command.output_file.read_text())
    keys = {series["series_key"] for series in content["telemetry_series"]}
    assert keys == {"linear_velocity", "velocity_x_only"}


def test_config_parsing_reads_the_builder_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "\n".join(
            [
                "[afft.benthloc.build_telemetry_ingestion_document]",
                "[[afft.benthloc.build_telemetry_ingestion_document.sensors]]",
                'sensor_key = "dvl_teledyne"',
                "[[afft.benthloc.build_telemetry_ingestion_document.series]]",
                'frame_key = "telemetry/dvl/linear_velocity"',
                'sensor_key = "dvl_teledyne"',
                'series_key = "linear_velocity"',
                'payload_schema_name = "linear_velocity"',
                'columns = { velx = "velx", vely = "vely", velz = "velz" }',
            ]
        )
    )

    config = read_build_telemetry_ingestion_document_config(config_file)

    assert len(config.sensors) == 1
    assert config.sensors[0].sensor_key == "dvl_teledyne"
    assert len(config.series) == 1
    assert config.series[0].series_key == "linear_velocity"
    assert config.series[0].columns == {
        "velx": "velx",
        "vely": "vely",
        "velz": "velz",
    }


def test_missing_builder_section_parses_to_empty_config(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("[afft.other]\nvalue = 1\n")

    config = read_build_telemetry_ingestion_document_config(config_file)

    assert config.sensors == []
    assert config.series == []


def test_series_referencing_unknown_sensor_raises(tmp_path: Path) -> None:
    config = _config(
        series=[
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "not_configured",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {"velx": "velx"},
            }
        ]
    )
    command = _command(tmp_path)

    with pytest.raises(ValueError, match="no SensorEntry"):
        run_build_telemetry_ingestion_document(command, config)


def test_duplicate_series_identity_raises(tmp_path: Path) -> None:
    series = {
        "frame_key": "telemetry/dvl/linear_velocity",
        "sensor_key": "dvl_teledyne",
        "series_key": "linear_velocity",
        "payload_schema_name": "linear_velocity",
        "columns": {"velx": "velx"},
    }
    config = _config(series=[series, dict(series)])
    command = _command(tmp_path)

    with pytest.raises(ValueError, match="duplicate"):
        run_build_telemetry_ingestion_document(command, config)


def test_config_sensor_absent_from_bundle_raises(tmp_path: Path) -> None:
    config = _config(
        sensors=[{"sensor_key": "absent_sensor"}],
        series=[
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "absent_sensor",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {"velx": "velx"},
            }
        ],
    )
    command = _command(tmp_path)

    with pytest.raises(ValueError, match="absent from the bundle"):
        run_build_telemetry_ingestion_document(command, config)


def test_missing_frame_column_fails_fast_on_write(tmp_path: Path) -> None:
    """A series naming a column absent from its frame collects an error and
    fails the non-dry run."""
    config = _config(
        series=[
            {
                "frame_key": "telemetry/dvl/linear_velocity",
                "sensor_key": "dvl_teledyne",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {"absent_column": "velx"},
            }
        ]
    )
    command = _command(tmp_path)

    with pytest.raises(ValueError, match="had errors"):
        run_build_telemetry_ingestion_document(command, config)


def test_absent_frame_is_warned_and_skipped(tmp_path: Path) -> None:
    """A series whose frame is absent is a warning, not an error, and is
    skipped rather than failing the run."""
    config = _config(
        series=[
            {
                "frame_key": "telemetry/dvl/absent",
                "sensor_key": "dvl_teledyne",
                "series_key": "linear_velocity",
                "payload_schema_name": "linear_velocity",
                "columns": {"velx": "velx"},
            }
        ]
    )
    command = _command(tmp_path)

    result = run_build_telemetry_ingestion_document(command, config)

    assert result.series_count == 0
    assert result.diagnostics.errors == []
    assert any(
        "absent" in warning.message for warning in result.diagnostics.warnings
    )


def test_missing_sensor_identity_is_warned(tmp_path: Path) -> None:
    """A configured sensor with no identity frame (but a discoverable
    extrinsics frame) is emitted with empty identity, and the gap is warned
    about."""
    bundle_file = _bundle(
        tmp_path / "bundle.gpkg",
        with_sensor_identity=False,
    )
    config = _config(
        sensors=[{"sensor_key": "dvl_teledyne"}],
    )
    command = _command(tmp_path, bundle_file=bundle_file)

    result = run_build_telemetry_ingestion_document(command, config)

    assert result.sensor_count == 1
    content = json.loads(command.output_file.read_text())
    sensor = content["telemetry_sensors"][0]
    assert sensor["sensor_label"] == ""
    assert len(sensor["extrinsics"]) == 1
    messages = {warning.message for warning in result.diagnostics.warnings}
    assert "sensor has no identity frame" in messages


def test_missing_sensor_extrinsics_is_warned(tmp_path: Path) -> None:
    """A configured sensor with no extrinsics frame (but a discoverable
    identity frame) is emitted with no extrinsics, and the gap is warned
    about."""
    bundle_file = _bundle(
        tmp_path / "bundle.gpkg",
        with_sensor_extrinsics=False,
    )
    config = _config(
        sensors=[{"sensor_key": "dvl_teledyne"}],
    )
    command = _command(tmp_path, bundle_file=bundle_file)

    result = run_build_telemetry_ingestion_document(command, config)

    assert result.sensor_count == 1
    content = json.loads(command.output_file.read_text())
    sensor = content["telemetry_sensors"][0]
    assert sensor["extrinsics"] == []
    messages = {warning.message for warning in result.diagnostics.warnings}
    assert "sensor has no extrinsics frame" in messages


def test_diagnostics_callbacks_accumulate() -> None:
    """The diagnostics collector's bound methods satisfy the callback
    aliases and accumulate warnings, errors, and drops."""
    diagnostics = TelemetryIngestionDiagnostics()

    diagnostics.warning("topic", "a warning")
    diagnostics.error("topic", "an error")
    diagnostics.drop_samples(3)

    assert len(diagnostics.warnings) == 1
    assert len(diagnostics.errors) == 1
    assert diagnostics.dropped_sample_count == 3
