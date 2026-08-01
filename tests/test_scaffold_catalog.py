"""Tests for the scaffold catalog task and its CLI."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    DeploymentDescriptor,
    DeploymentFileSection,
    DeploymentMetadata,
    DeploymentPlatformSection,
    DeploymentSystemSection,
    DeploymentTelemetrySection,
    PlatformSensor,
    read_deployment_catalog,
    write_deployment_descriptors,
)
from afft.tasks.deployment_catalog import (
    ScaffoldCatalogCommand,
    ScaffoldCatalogDiagnostics,
    run_scaffold_catalog,
    scaffold_catalog,
)


def _build_descriptor(
    label: str,
    moment: datetime,
    campaign: str,
    sensor_keys: tuple[str, ...],
    usbl_logs: tuple[str, ...] = ("usbl/log-1.txt",),
) -> DeploymentDescriptor:
    """Builds a descriptor carrying only the fields the scaffolder reads."""
    return DeploymentDescriptor(
        deployment_label=label,
        deployment_datetime=moment,
        metadata=DeploymentMetadata(
            acfr_deployment_label=label,
            acfr_campaign_label=campaign,
            acfr_platform_label="",
            origin_latitude=-28.8,
            origin_longitude=113.9,
            magnetic_variation=-1.16,
        ),
        files=DeploymentFileSection(usbl_logs=list(usbl_logs)),
        telemetry=DeploymentTelemetrySection(topics=[]),
        platform=DeploymentPlatformSection(
            sensors=[PlatformSensor(key=key) for key in sensor_keys]
        ),
        system=DeploymentSystemSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["RAW"],
        ),
    )


@pytest.fixture
def descriptors() -> list[DeploymentDescriptor]:
    """Two deployments in one year and campaign, plus one in the next year."""
    return [
        _build_descriptor(
            "qdch0ftq_20100428_020202",
            datetime(2010, 4, 28, 2, 2, 2, tzinfo=timezone.utc),
            "WA201004",
            ("RDI", "VIS"),
        ),
        _build_descriptor(
            "qd61g27j_20100421_022145",
            datetime(2010, 4, 21, 2, 21, 45, tzinfo=timezone.utc),
            "WA201004",
            ("RDI", "PAROSCI"),
        ),
        _build_descriptor(
            "qdch0ftq_20110415_020103",
            datetime(2011, 4, 15, 2, 1, 3, tzinfo=timezone.utc),
            "WA201104",
            ("RDI",),
            usbl_logs=(),
        ),
    ]


def test_platform_profiles_are_grouped_per_year(
    descriptors: list[DeploymentDescriptor],
) -> None:
    catalog = scaffold_catalog(descriptors, ScaffoldCatalogDiagnostics())

    assert [profile.key for profile in catalog.platform_profiles] == [
        "2010_seabed",
        "2011_seabed",
    ]
    assert catalog.platform_profiles[0].platform_class == "SEABED"


def test_platform_profile_sensors_are_the_union_of_the_year(
    descriptors: list[DeploymentDescriptor],
) -> None:
    catalog = scaffold_catalog(descriptors, ScaffoldCatalogDiagnostics())

    profile = catalog.platform_profiles[0]
    assert [sensor.key for sensor in profile.sensors] == [
        "PAROSCI",
        "RDI",
        "VIS",
    ]
    assert [sensor.identity for sensor in profile.sensors] == [
        "parosci",
        "rdi",
        "vis",
    ]
    assert all(sensor.extrinsics is None for sensor in profile.sensors)


def test_sensor_stubs_cover_every_observed_key(
    descriptors: list[DeploymentDescriptor],
) -> None:
    catalog = scaffold_catalog(descriptors, ScaffoldCatalogDiagnostics())

    assert [sensor.key for sensor in catalog.sensor_identities] == [
        "parosci",
        "rdi",
        "vis",
    ]
    assert all(sensor.vendor == "" for sensor in catalog.sensor_identities)


def test_vessel_profiles_are_grouped_per_campaign(
    descriptors: list[DeploymentDescriptor],
) -> None:
    catalog = scaffold_catalog(descriptors, ScaffoldCatalogDiagnostics())

    assert [profile.key for profile in catalog.vessel_profiles] == [
        "201004_wa201004"
    ]
    assert catalog.vessel_profiles[0].vessel_name == ""
    assert catalog.vessel_profiles[0].sensors == []


def test_deployments_without_usbl_logs_get_no_vessel(
    descriptors: list[DeploymentDescriptor],
) -> None:
    diagnostics = ScaffoldCatalogDiagnostics()

    catalog = scaffold_catalog(descriptors, diagnostics)

    # Both tables are sorted by deployment label, not left in descriptor order.
    assert [
        entry.deployment_label for entry in catalog.deployment_platforms
    ] == [
        "qd61g27j_20100421_022145",
        "qdch0ftq_20100428_020202",
        "qdch0ftq_20110415_020103",
    ]
    assert [entry.deployment_label for entry in catalog.deployment_vessels] == [
        "qd61g27j_20100421_022145",
        "qdch0ftq_20100428_020202",
    ]
    assert [warning.deployment_label for warning in diagnostics.warnings] == [
        "qdch0ftq_20110415_020103"
    ]


def test_mappings_reference_the_derived_profile_keys(
    descriptors: list[DeploymentDescriptor],
) -> None:
    catalog = scaffold_catalog(descriptors, ScaffoldCatalogDiagnostics())

    assert catalog.deployment_platforms[2].platform_profile == "2011_seabed"
    assert catalog.deployment_vessels[0].vessel_profile == "201004_wa201004"


def test_run_writes_a_readable_catalog(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file = tmp_path / "descriptors.toml"
    output_file = tmp_path / "catalog.toml"
    write_deployment_descriptors(input_file, descriptors)

    result = run_scaffold_catalog(
        ScaffoldCatalogCommand(input_file=input_file, output_file=output_file)
    )

    assert read_deployment_catalog(output_file) == result.catalog


def test_run_rejects_an_empty_descriptors_file(tmp_path: Path) -> None:
    input_file = tmp_path / "descriptors.toml"
    write_deployment_descriptors(input_file, [])

    with pytest.raises(ValueError, match="no deployments"):
        run_scaffold_catalog(
            ScaffoldCatalogCommand(
                input_file=input_file, output_file=tmp_path / "catalog.toml"
            )
        )


def test_cli_scaffolds_a_catalog(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file = tmp_path / "descriptors.toml"
    output_file = tmp_path / "catalog.toml"
    write_deployment_descriptors(input_file, descriptors)

    result: Result = CliRunner().invoke(
        cli,
        [
            "deployment",
            "scaffold-catalog",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(read_deployment_catalog(output_file).platform_profiles) == 2
