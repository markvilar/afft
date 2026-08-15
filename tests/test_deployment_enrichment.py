"""Tests for the deployment descriptor enrichment tasks and their CLI."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    DeploymentMetadata,
    EnrichmentSection,
    FileDescriptorSection,
    PlatformDescriptorSection,
    SystemDescriptorSection,
    TelemetryDescriptorSection,
    enrich_descriptor,
    read_deployment_descriptors,
    write_deployment_catalog,
    write_deployment_descriptors,
)
from afft.squidle import Campaign, Deployment, Platform, SquidleClient
from afft.tasks.deployment_enrichment import (
    DeploymentMatchPolicy,
    EnrichCatalogCommand,
    EnrichCatalogDiagnostics,
    enrich_descriptors,
    enrich_descriptors_from_catalog,
    match_squidle_deployments,
)

PLATFORM_LABEL: str = "qdch0ftq_20100428_020202"
UNASSIGNED_LABEL: str = "qd61g27j_20100421_022145"


def _build_descriptor(
    label: str,
    topics: tuple[str, ...] = ("RDI", "VIS", "MICRON"),
) -> DeploymentDescriptor:
    """Builds a descriptor carrying only the fields enrichment reads."""
    return DeploymentDescriptor(
        deployment_label=label,
        deployment_start_datetime=datetime(
            2010, 4, 28, 2, 2, 2, tzinfo=timezone.utc
        ),
        metadata=DeploymentMetadata(
            acfr_deployment_label=label,
            acfr_campaign_label="WA201004",
            acfr_platform_label="",
            origin_latitude=-28.8,
            origin_longitude=113.9,
            magnetic_variation=-1.16,
        ),
        files=FileDescriptorSection(),
        telemetry=TelemetryDescriptorSection(topics=list(topics)),
        platform=PlatformDescriptorSection(),
        system=SystemDescriptorSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["RAW"],
            sensors=["RDI", "VIS", "MICRON"],
        ),
    )


def _build_catalog() -> DeploymentCatalog:
    """
    Builds a catalog assigning both profiles to one deployment and neither to
    the other, with a platform profile mounting a sensor the system config
    roster does not name — the multibeam — and leaving one it does name — the
    MICRON sonar — unmounted.
    """
    return DeploymentCatalog(
        sensor_identities=[
            CatalogSensorIdentity(
                key="dvl_teledyne_navigator",
                label="Teledyne RDI Work Horse Navigator DVL",
                vendor="Teledyne RDI",
                product="Work Horse Navigator",
                type="dvl",
            ),
            CatalogSensorIdentity(
                key="camera_avt_prosilica",
                label="AVT Prosilica GC1380 stereo camera",
                vendor="AVT",
                product="Prosilica GC1380",
                type="stereo_camera",
            ),
            CatalogSensorIdentity(
                key="multibeam_deltat",
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
                        key="dvl_teledyne_navigator",
                        message_topics=["RDI"],
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
                        key="camera_avt_prosilica", message_topics=["VIS"]
                    ),
                    # Mounted though the system config names no channel for
                    # it, and emitting no topic of its own.
                    CatalogProfileSensor(key="multibeam_deltat"),
                ],
            )
        ],
        vessel_profiles=[
            CatalogVesselProfile(
                key="201004_wa201004",
                vessel_name="RV Linnaeus",
                sensors=[
                    CatalogProfileSensor(
                        key="usbl_evologics_transceiver",
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
    assert dvl.key == "dvl_teledyne_navigator"
    assert dvl.message_topics == ["RDI"]
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
    assert camera.key == "camera_avt_prosilica"
    assert camera.identity is not None
    assert camera.identity.product == "Prosilica GC1380"
    assert camera.extrinsics is None


def test_platform_roster_comes_wholly_from_the_profile(
    index: DeploymentCatalogIndex,
) -> None:
    descriptor = _build_descriptor(PLATFORM_LABEL)

    enrichment = enrich_descriptor(descriptor, index)

    # The multibeam is mounted though the system config roster omits it, and
    # the MICRON sonar the roster names is left off, since no profile mounts
    # it.
    assert [
        sensor.key for sensor in enrichment.descriptor.platform.sensors
    ] == [
        "dvl_teledyne_navigator",
        "camera_avt_prosilica",
        "multibeam_deltat",
    ]
    assert descriptor.system.sensors == ["RDI", "VIS", "MICRON"]


def test_topic_mismatches_are_reported_in_both_directions(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(
        _build_descriptor(PLATFORM_LABEL, topics=("RDI", "MICRON")), index
    )

    assert enrichment.undeclared_topics == ["MICRON"]
    assert enrichment.unobserved_topics == ["VIS"]


def test_matching_topics_are_not_reported(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(
        _build_descriptor(PLATFORM_LABEL, topics=("RDI", "VIS")), index
    )

    assert enrichment.undeclared_topics == []
    assert enrichment.unobserved_topics == []


def test_topics_are_not_compared_without_a_platform_profile(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(UNASSIGNED_LABEL), index)

    assert enrichment.undeclared_topics == []
    assert enrichment.unobserved_topics == []


def test_vessel_section_is_filled_entirely_from_the_profile(
    index: DeploymentCatalogIndex,
) -> None:
    enrichment = enrich_descriptor(_build_descriptor(PLATFORM_LABEL), index)

    vessel = enrichment.descriptor.vessel
    assert enrichment.vessel_matched is True
    assert vessel.identity is not None
    assert vessel.identity.vessel_name == "RV Linnaeus"
    assert [sensor.key for sensor in vessel.sensors] == [
        "usbl_evologics_transceiver"
    ]

    modem = vessel.sensors[0]
    # The transceiver's data arrives through the usbl_logs file role.
    assert modem.message_topics == []
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
    diagnostics = EnrichCatalogDiagnostics()

    enrich_descriptors(descriptors, catalog, diagnostics)

    assert [
        (warning.deployment_label, warning.message)
        for warning in diagnostics.warnings
    ] == [
        (
            PLATFORM_LABEL,
            "logged topics no curated sensor claims: MICRON",
        ),
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
    diagnostics = EnrichCatalogDiagnostics()

    enrich_descriptors(
        descriptors, catalog, diagnostics, EnrichmentSection.VESSEL
    )

    assert [warning.message for warning in diagnostics.warnings] == [
        "no vessel profile assigned"
    ]


def test_topic_mismatches_are_warned_about(
    descriptors: list[DeploymentDescriptor], catalog: DeploymentCatalog
) -> None:
    diagnostics = EnrichCatalogDiagnostics()

    enrich_descriptors(descriptors, catalog, diagnostics)

    assert [
        warning.message
        for warning in diagnostics.warnings
        if warning.deployment_label == PLATFORM_LABEL
    ] == ["logged topics no curated sensor claims: MICRON"]


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

    result = enrich_descriptors_from_catalog(
        EnrichCatalogCommand(
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
    command = EnrichCatalogCommand(
        input_file=input_file,
        catalog_file=catalog_file,
        output_file=input_file,
    )

    enrich_descriptors_from_catalog(command)
    once = input_file.read_bytes()
    enrich_descriptors_from_catalog(command)

    assert input_file.read_bytes() == once
    assert (
        read_deployment_descriptors(input_file)[0].vessel.identity is not None
    )


def test_run_rejects_a_missing_catalog(
    tmp_path: Path, descriptors: list[DeploymentDescriptor]
) -> None:
    input_file, _ = _write_inputs(tmp_path, descriptors)

    with pytest.raises(FileNotFoundError, match="catalog file"):
        enrich_descriptors_from_catalog(
            EnrichCatalogCommand(
                input_file=input_file,
                catalog_file=tmp_path / "absent.toml",
                output_file=tmp_path / "enriched.toml",
            )
        )


def test_run_rejects_an_empty_descriptors_file(tmp_path: Path) -> None:
    input_file, catalog_file = _write_inputs(tmp_path, [])

    with pytest.raises(ValueError, match="no deployments"):
        enrich_descriptors_from_catalog(
            EnrichCatalogCommand(
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
            "enrich-catalog",
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
            "enrich-catalog",
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


MATCHED_LABEL: str = "qdch0ftq_20100428_020202"
AMBIGUOUS_LABEL: str = "qd9xyz00_20100503_101010"


class _FakeSquidleClient(SquidleClient):
    """
    Fake Squidle+ client for tests, backed by in-memory fixtures.

    Skips ``SquidleClient.__init__`` entirely, so no HTTP transport is ever
    created; only the three methods ``match_squidle_deployments`` calls are
    overridden.
    """

    def __init__(
        self,
        deployments: list[Deployment],
        campaigns: dict[int, Campaign],
        platforms: dict[int, Platform],
        failing_campaign_ids: frozenset[int] = frozenset(),
        failing_platform_ids: frozenset[int] = frozenset(),
    ) -> None:
        self._deployments = deployments
        self._campaigns = campaigns
        self._platforms = platforms
        self._failing_campaign_ids = failing_campaign_ids
        self._failing_platform_ids = failing_platform_ids
        self.campaign_calls: list[int] = []
        self.platform_calls: list[int] = []

    def fetch_deployments(
        self, filters: list[dict[str, Any]] | None = None
    ) -> list[Deployment]:
        assert filters is not None
        field: str = filters[0]["name"]
        value: str = filters[0]["val"]
        if field == "name":
            return [d for d in self._deployments if d.name == value]
        stripped: str = value.strip("%")
        return [d for d in self._deployments if stripped in d.key]

    def fetch_campaign(self, campaign_id: int) -> Campaign:
        self.campaign_calls.append(campaign_id)
        if campaign_id in self._failing_campaign_ids:
            raise RuntimeError(f"campaign fetch failed: {campaign_id}")
        return self._campaigns[campaign_id]

    def fetch_platform(self, platform_id: int) -> Platform:
        self.platform_calls.append(platform_id)
        if platform_id in self._failing_platform_ids:
            raise RuntimeError(f"platform fetch failed: {platform_id}")
        return self._platforms[platform_id]


def _build_squidle_deployment(
    label: str,
    deployment_id: int,
    campaign_id: int = 10,
    platform_id: int = 100,
    datetime_key: str | None = None,
) -> Deployment:
    key_source: str = datetime_key if datetime_key is not None else label
    return Deployment(
        id=deployment_id,
        key=f"r{_squidle_key_suffix(key_source)}_dep{deployment_id}",
        name=label,
        campaign_id=campaign_id,
        campaign_name="Campaign A",
        platform_id=platform_id,
        platform_name="AUV Sirius",
        timestamp_start=None,
        timestamp_end=None,
        media_count=0,
        pose_count=0,
        is_valid=True,
    )


def _squidle_key_suffix(deployment_label: str) -> str:
    parts: list[str] = deployment_label.rsplit("_", 2)
    return f"{parts[-2]}_{parts[-1]}"


def test_match_squidle_deployments_fills_the_squidle_section() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(MATCHED_LABEL)
    deployment: Deployment = _build_squidle_deployment(MATCHED_LABEL, 1)
    client = _FakeSquidleClient(
        deployments=[deployment],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 1, 1)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
    )

    enriched = match_squidle_deployments([descriptor], client)

    squidle = enriched[0].squidle
    assert squidle.deployment_id == 1
    assert squidle.deployment_name == MATCHED_LABEL
    assert squidle.campaign_key == "camp-a"
    assert squidle.platform_key == "plat-sirius"


def test_no_match_leaves_the_squidle_section_at_defaults() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(UNASSIGNED_LABEL)
    client = _FakeSquidleClient(deployments=[], campaigns={}, platforms={})

    enriched = match_squidle_deployments([descriptor], client)

    assert enriched[0].squidle.deployment_id is None


def test_ambiguous_match_is_treated_as_no_match() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(AMBIGUOUS_LABEL)
    client = _FakeSquidleClient(
        deployments=[
            _build_squidle_deployment(AMBIGUOUS_LABEL, 1),
            _build_squidle_deployment(AMBIGUOUS_LABEL, 2),
        ],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 1, 1)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
    )

    enriched = match_squidle_deployments([descriptor], client)

    assert enriched[0].squidle.deployment_id is None


def test_by_key_policy_matches_on_the_embedded_datetime() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(MATCHED_LABEL)
    deployment: Deployment = _build_squidle_deployment(
        "some other squidle name", 1, datetime_key=MATCHED_LABEL
    )
    client = _FakeSquidleClient(
        deployments=[deployment],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 1, 1)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
    )

    enriched = match_squidle_deployments(
        [descriptor], client, policy=DeploymentMatchPolicy.BY_KEY
    )

    assert enriched[0].squidle.deployment_id == 1


def test_campaign_lookup_failure_keeps_the_deployment_match() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(MATCHED_LABEL)
    deployment: Deployment = _build_squidle_deployment(MATCHED_LABEL, 1)
    client = _FakeSquidleClient(
        deployments=[deployment],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 1, 1)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
        failing_campaign_ids=frozenset({10}),
    )

    enriched = match_squidle_deployments([descriptor], client)

    squidle = enriched[0].squidle
    assert squidle.deployment_id == 1
    assert squidle.campaign_key is None
    assert squidle.platform_key == "plat-sirius"


def test_platform_lookup_failure_keeps_the_deployment_match() -> None:
    descriptor: DeploymentDescriptor = _build_descriptor(MATCHED_LABEL)
    deployment: Deployment = _build_squidle_deployment(MATCHED_LABEL, 1)
    client = _FakeSquidleClient(
        deployments=[deployment],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 1, 1)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
        failing_platform_ids=frozenset({100}),
    )

    enriched = match_squidle_deployments([descriptor], client)

    squidle = enriched[0].squidle
    assert squidle.deployment_id == 1
    assert squidle.campaign_key == "camp-a"
    assert squidle.platform_key is None


def test_campaign_and_platform_lookups_are_cached_across_deployments() -> None:
    label_a: str = MATCHED_LABEL
    label_b: str = UNASSIGNED_LABEL
    client = _FakeSquidleClient(
        deployments=[
            _build_squidle_deployment(label_a, 1),
            _build_squidle_deployment(label_b, 2),
        ],
        campaigns={10: Campaign(10, "camp-a", "Campaign A", 2, 2)},
        platforms={100: Platform(100, "plat-sirius", "AUV Sirius")},
    )

    match_squidle_deployments(
        [_build_descriptor(label_a), _build_descriptor(label_b)],
        client,
        max_workers=1,
    )

    assert client.campaign_calls == [10]
    assert client.platform_calls == [100]
