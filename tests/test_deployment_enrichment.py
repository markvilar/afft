"""Tests for the deployment descriptor enrichment task and its CLI."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    CatalogDeploymentPlatform,
    CatalogDeploymentVessel,
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensorExtrinsics,
    CatalogSensorIdentity,
    CatalogVesselProfile,
    DeploymentCatalog,
    DeploymentCatalogIndex,
    DeploymentDescriptor,
    DeploymentFileSection,
    DeploymentMetadata,
    DeploymentPlatformSection,
    DeploymentSystemSection,
    DeploymentTelemetrySection,
    EnrichmentSection,
    PlatformSensor,
    enrich_descriptor,
    read_deployment_descriptors,
    write_deployment_catalog,
    write_deployment_descriptors,
)
from afft.tasks.deployment_enrichment import (
    EnrichDescriptorCommand,
    EnrichDescriptorDiagnostics,
    enrich_descriptors,
    run_enrich_descriptor,
)

PLATFORM_LABEL: str = "qdch0ftq_20100428_020202"
UNASSIGNED_LABEL: str = "qd61g27j_20100421_022145"


def _build_descriptor(
    label: str,
    sensor_keys: tuple[str, ...] = ("RDI", "VIS", "MICRON"),
) -> DeploymentDescriptor:
    """Builds a descriptor carrying only the fields enrichment reads."""
    return DeploymentDescriptor(
        deployment_label=label,
        deployment_datetime=datetime(2010, 4, 28, 2, 2, 2, tzinfo=timezone.utc),
        metadata=DeploymentMetadata(
            acfr_deployment_label=label,
            acfr_campaign_label="WA201004",
            acfr_platform_label="",
            origin_latitude=-28.8,
            origin_longitude=113.9,
            magnetic_variation=-1.16,
        ),
        files=DeploymentFileSection(),
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


def _build_catalog() -> DeploymentCatalog:
    """
    Builds a catalog assigning both profiles to one deployment and neither to
    the other, with a platform profile carrying an entry — ``DELTA_T`` — that
    no roster names and lacking one — ``MICRON`` — that every roster does.
    """
    return DeploymentCatalog(
        sensor_identities=[
            CatalogSensorIdentity(
                key="dvl_teledyne",
                label="Teledyne RDI Work Horse Navigator DVL",
                vendor="Teledyne RDI",
                product="Work Horse Navigator",
                type="dvl",
            ),
            CatalogSensorIdentity(
                key="camera_prosilica",
                label="AVT Prosilica GC1380 stereo camera",
                vendor="AVT",
                product="Prosilica GC1380",
                type="stereo_camera",
            ),
            CatalogSensorIdentity(
                key="sonar_deltat",
                label="Imagenex DeltaT multibeam sonar",
                vendor="Imagenex",
                product="DeltaT 837B",
                type="multibeam_sonar",
            ),
            CatalogSensorIdentity(
                key="usbl_evologics_transceiver",
                label="EvoLogics S2CR USBL transceiver",
                vendor="EvoLogics",
                product="S2CR 18/34",
                type="usbl",
            ),
        ],
        platform_profiles=[
            CatalogPlatformProfile(
                key="2010_seabed",
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="ACFR",
                sensors=[
                    CatalogProfileSensor(
                        key="RDI",
                        identity="dvl_teledyne",
                        extrinsics=CatalogSensorExtrinsics(
                            locx=0.55,
                            locy=0.0,
                            locz=0.28,
                            rotx=0.0,
                            roty=0.0,
                            rotz=-0.785,
                        ),
                    ),
                    # Curated without a surveyed pose, the common outcome.
                    CatalogProfileSensor(
                        key="VIS", identity="camera_prosilica"
                    ),
                    # Carried by the profile but named by no roster.
                    CatalogProfileSensor(
                        key="DELTA_T", identity="sonar_deltat"
                    ),
                ],
            )
        ],
        vessel_profiles=[
            CatalogVesselProfile(
                key="201004_wa201004",
                vessel_name="RV Linnaeus",
                sensors=[
                    CatalogProfileSensor(
                        key="USBL",
                        identity="usbl_evologics_transceiver",
                        extrinsics=CatalogSensorExtrinsics(
                            locx=1.2,
                            locy=-0.4,
                            locz=3.1,
                            rotx=0.0,
                            roty=0.0,
                            rotz=1.571,
                        ),
                    )
                ],
            )
        ],
        deployment_platforms=[
            CatalogDeploymentPlatform(
                deployment_label=PLATFORM_LABEL,
                platform_profile="2010_seabed",
            )
        ],
        deployment_vessels=[
            CatalogDeploymentVessel(
                deployment_label=PLATFORM_LABEL,
                vessel_profile="201004_wa201004",
            )
        ],
    )


@pytest.fixture
def catalog() -> DeploymentCatalog:
    """The curated catalog under test."""
    return _build_catalog()


@pytest.fixture
def index(catalog: DeploymentCatalog) -> DeploymentCatalogIndex:
    """The catalog indexed for lookup."""
    return DeploymentCatalogIndex.from_catalog(catalog)


@pytest.fixture
def descriptors() -> list[DeploymentDescriptor]:
    """One fully assigned deployment and one with no assignment at all."""
    return [
        _build_descriptor(PLATFORM_LABEL),
        _build_descriptor(UNASSIGNED_LABEL),
    ]


def test_matched_sensor_gets_its_identity_and_extrinsics(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    platform = enrichment.descriptor.platform
    assert enrichment.platform_matched is True
    assert platform.identity is not None
    assert platform.identity.platform_label == "AUV Sirius"
    assert platform.identity.platform_class == "SEABED"
    assert platform.identity.platform_operator == "ACFR"

    dvl = platform.sensors[0]
    assert dvl.key == "RDI"
    assert dvl.identity is not None
    assert dvl.identity.vendor == "Teledyne RDI"
    assert dvl.extrinsics is not None
    assert dvl.extrinsics.locx == 0.55
    assert dvl.extrinsics.rotz == -0.785


def test_catalog_entry_without_extrinsics_fills_identity_only(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    camera = enrichment.descriptor.platform.sensors[1]
    assert camera.key == "VIS"
    assert camera.identity is not None
    assert camera.identity.product == "Prosilica GC1380"
    assert camera.extrinsics is None


def test_roster_key_absent_from_the_profile_stays_unfilled(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    sonar = enrichment.descriptor.platform.sensors[2]
    assert sonar.key == "MICRON"
    assert sonar.identity is None
    assert sonar.extrinsics is None


def test_profile_entry_absent_from_the_roster_is_not_added(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    assert [
        sensor.key for sensor in enrichment.descriptor.platform.sensors
    ] == ["RDI", "VIS", "MICRON"]


def test_vessel_section_is_filled_entirely_from_the_profile(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    vessel = enrichment.descriptor.vessel
    assert enrichment.vessel_matched is True
    assert vessel.identity is not None
    assert vessel.identity.vessel_name == "RV Linnaeus"
    assert [sensor.key for sensor in vessel.sensors] == ["USBL"]

    modem = vessel.sensors[0]
    assert modem.identity is not None
    assert modem.identity.type == "usbl"
    assert modem.extrinsics is not None
    assert modem.extrinsics.locz == 3.1


def test_deployment_without_assignments_keeps_its_empty_slots(
    index: DeploymentCatalogIndex,
) -> None:
    descriptor = _build_descriptor(UNASSIGNED_LABEL)

    enrichment = enrich_descriptor(descriptor, index)

    assert enrichment.platform_matched is False
    assert enrichment.vessel_matched is False
    assert enrichment.descriptor == descriptor


def test_missing_assignments_are_warned_about_per_section(
    descriptors: list[DeploymentDescriptor], catalog: DeploymentCatalog
) -> None:
    diagnostics = EnrichDescriptorDiagnostics()

    enrich_descriptors(descriptors, catalog, diagnostics)

    assert [
        (warning.deployment_label, warning.message)
        for warning in diagnostics.warnings
    ] == [
        (UNASSIGNED_LABEL, "no platform profile assigned"),
        (UNASSIGNED_LABEL, "no vessel profile assigned"),
    ]


def test_platform_section_leaves_the_vessel_untouched(
    index: DeploymentCatalogIndex,
) -> None:
    descriptor = _build_descriptor(PLATFORM_LABEL)

    enrichment = enrich_descriptor(
        descriptor, index, EnrichmentSection.PLATFORM
    )

    assert enrichment.descriptor.platform.identity is not None
    assert enrichment.descriptor.vessel == descriptor.vessel
    assert enrichment.platform_matched is True
    assert enrichment.vessel_matched is None


def test_vessel_section_leaves_the_platform_untouched(
    index: DeploymentCatalogIndex,
) -> None:
    descriptor = _build_descriptor(PLATFORM_LABEL)

    enrichment = enrich_descriptor(descriptor, index, EnrichmentSection.VESSEL)

    assert enrichment.descriptor.vessel.identity is not None
    assert enrichment.descriptor.platform == descriptor.platform
    assert enrichment.platform_matched is None
    assert enrichment.vessel_matched is True


def test_unrequested_section_is_not_warned_about(
    descriptors: list[DeploymentDescriptor], catalog: DeploymentCatalog
) -> None:
    diagnostics = EnrichDescriptorDiagnostics()

    enrich_descriptors(
        descriptors, catalog, diagnostics, EnrichmentSection.VESSEL
    )

    assert [warning.message for warning in diagnostics.warnings] == [
        "no vessel profile assigned"
    ]


def _write_inputs(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> tuple[Path, Path]:
    """Writes the descriptors and catalog files, returning their paths."""
    input_file = tmp_path / "descriptors.toml"
    catalog_file = tmp_path / "catalog.toml"
    write_deployment_descriptors(input_file, descriptors)
    write_deployment_catalog(catalog_file, _build_catalog())
    return input_file, catalog_file


def test_run_writes_a_readable_descriptors_file(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, descriptors)
    output_file = tmp_path / "enriched.toml"

    result = run_enrich_descriptor(
        EnrichDescriptorCommand(
            input_file=input_file,
            catalog_file=catalog_file,
            output_file=output_file,
        )
    )

    assert read_deployment_descriptors(output_file) == result.descriptors


def test_run_enriches_in_place_and_is_idempotent(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, descriptors)
    command = EnrichDescriptorCommand(
        input_file=input_file,
        catalog_file=catalog_file,
        output_file=input_file,
    )

    run_enrich_descriptor(command)
    once = input_file.read_bytes()
    run_enrich_descriptor(command)

    assert input_file.read_bytes() == once
    assert (
        read_deployment_descriptors(input_file)[0].vessel.identity is not None
    )


def test_run_rejects_a_missing_catalog(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, _ = _write_inputs(tmp_path, descriptors)

    with pytest.raises(FileNotFoundError, match="catalog file"):
        run_enrich_descriptor(
            EnrichDescriptorCommand(
                input_file=input_file,
                catalog_file=tmp_path / "absent.toml",
                output_file=tmp_path / "enriched.toml",
            )
        )


def test_run_rejects_an_empty_descriptors_file(tmp_path: Path) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, [])

    with pytest.raises(ValueError, match="no deployments"):
        run_enrich_descriptor(
            EnrichDescriptorCommand(
                input_file=input_file,
                catalog_file=catalog_file,
                output_file=tmp_path / "enriched.toml",
            )
        )


def test_cli_enriches_descriptors(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, descriptors)
    output_file = tmp_path / "enriched.toml"

    result: Result = CliRunner().invoke(
        cli,
        [
            "deployment",
            "enrich",
            "--input",
            str(input_file),
            "--catalog",
            str(catalog_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    enriched = read_deployment_descriptors(output_file)
    assert enriched[0].platform.identity is not None
    assert enriched[0].vessel.identity is not None
    # The unassigned deployment is a curation gap, not a failure.
    assert enriched[1].platform.identity is None


def test_cli_enriches_only_the_requested_section(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, descriptors)
    output_file = tmp_path / "enriched.toml"

    result: Result = CliRunner().invoke(
        cli,
        [
            "deployment",
            "enrich",
            "--input",
            str(input_file),
            "--catalog",
            str(catalog_file),
            "--output",
            str(output_file),
            "--section",
            "platform",
        ],
    )

    assert result.exit_code == 0, result.output
    enriched = read_deployment_descriptors(output_file)
    assert enriched[0].platform.identity is not None
    assert enriched[0].vessel.identity is None
