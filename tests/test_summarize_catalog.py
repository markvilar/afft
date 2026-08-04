"""Tests for the summarize catalog task and its CLI."""

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
    CatalogSummary,
    CatalogVesselProfile,
    DeploymentCatalog,
    collect_unreferenced_sensors,
    summarize_catalog,
    write_deployment_catalog,
)
from afft.tasks.deployment_catalog import (
    SummarizeCatalogCommand,
    SummarizeCatalogResult,
    run_summarize_catalog,
)


def _extrinsics() -> CatalogSensorExtrinsics:
    """Builds a filled mounting pose."""
    return CatalogSensorExtrinsics(
        locx=0.1, locy=0.2, locz=0.3, rotx=0.0, roty=0.0, rotz=0.0
    )


def _sensor_identity(
    key: str = "dvl_teledyne",
    vendor: str = "Teledyne RDI",
) -> CatalogSensorIdentity:
    """Builds a sensor identity, optionally with an empty vendor."""
    return CatalogSensorIdentity(
        key=key,
        label="Doppler velocity log",
        vendor=vendor,
        product="Work Horse Navigator",
        type="dvl",
    )


def _build_catalog() -> DeploymentCatalog:
    """Builds a fully curated catalog covering two deployments."""
    return DeploymentCatalog(
        sensor_identities=[_sensor_identity()],
        platform_profiles=[
            CatalogPlatformProfile(
                key="sirius_2010",
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="ACFR",
                sensors=[
                    CatalogProfileSensor(
                        key="RDI",
                        identity="dvl_teledyne",
                        extrinsics=_extrinsics(),
                    )
                ],
            )
        ],
        vessel_profiles=[
            CatalogVesselProfile(key="linnaeus", vessel_name="RV Linnaeus")
        ],
        deployment_platforms=[
            CatalogDeploymentPlatform(
                deployment_label="aaa_20100428_020202",
                platform_profile="sirius_2010",
            ),
            CatalogDeploymentPlatform(
                deployment_label="bbb_20110415_020103",
                platform_profile="sirius_2010",
            ),
        ],
        deployment_vessels=[
            CatalogDeploymentVessel(
                deployment_label="aaa_20100428_020202",
                vessel_profile="linnaeus",
            ),
            CatalogDeploymentVessel(
                deployment_label="bbb_20110415_020103",
                vessel_profile="linnaeus",
            ),
        ],
    )


def test_summarize_counts_records_and_coverage() -> None:
    """Record counts and coverage aggregate over the whole catalog."""
    summary: CatalogSummary = summarize_catalog(_build_catalog())

    assert summary.sensor_identity_count == 1
    assert summary.platform_profile_count == 1
    assert summary.vessel_profile_count == 1
    assert summary.coverage.deployment_count == 2
    assert summary.coverage.with_platform == 2
    assert summary.coverage.with_vessel == 2
    assert not summary.coverage.platform_only
    assert not summary.coverage.vessel_only
    assert not summary.unreferenced_sensors
    assert not summary.curation_gaps


def test_summarize_reports_deployments_missing_an_assignment() -> None:
    """A deployment assigned only one profile is named as such."""
    catalog: DeploymentCatalog = _build_catalog()
    catalog = catalog.model_copy(
        update={"deployment_vessels": catalog.deployment_vessels[:1]}
    )

    summary: CatalogSummary = summarize_catalog(catalog)

    assert summary.coverage.deployment_count == 2
    assert summary.coverage.with_platform == 2
    assert summary.coverage.with_vessel == 1
    assert summary.coverage.platform_only == ["bbb_20110415_020103"]
    assert not summary.coverage.vessel_only


def test_summarize_lists_profiles_assigned_no_deployment() -> None:
    """Profiles carry their assignment count, zero included."""
    catalog: DeploymentCatalog = _build_catalog()
    catalog = catalog.model_copy(
        update={
            "platform_profiles": [
                *catalog.platform_profiles,
                CatalogPlatformProfile(
                    key="sirius_2011",
                    platform_label="AUV Sirius",
                    platform_class="SEABED",
                    platform_operator="ACFR",
                ),
            ]
        }
    )

    summary: CatalogSummary = summarize_catalog(catalog)
    counts: dict[str, int] = {
        assignment.profile_key: assignment.count
        for assignment in summary.platform_assignments
    }

    assert counts == {"sirius_2010": 2, "sirius_2011": 0}
    assert summary.platform_assignments[0].profile_key == "sirius_2010"
    assert summary.platform_assignments[0].deployment_labels == [
        "aaa_20100428_020202",
        "bbb_20110415_020103",
    ]


def test_summarize_reports_unreferenced_sensor_identities() -> None:
    """A sensor identity no profile mounts is reported as unused."""
    catalog: DeploymentCatalog = _build_catalog()
    catalog = catalog.model_copy(
        update={
            "sensor_identities": [
                *catalog.sensor_identities,
                _sensor_identity(key="usbl_linkquest_transceiver"),
            ]
        }
    )

    summary: CatalogSummary = summarize_catalog(catalog)

    assert summary.unreferenced_sensors == ["usbl_linkquest_transceiver"]
    assert collect_unreferenced_sensors(catalog) == [
        "usbl_linkquest_transceiver"
    ]


def test_summarize_groups_curation_gaps_by_field() -> None:
    """Gaps group by field and carry the records they affect."""
    catalog = DeploymentCatalog(
        sensor_identities=[_sensor_identity(vendor="")],
        platform_profiles=[
            CatalogPlatformProfile(
                key="sirius_2010",
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="",
                sensors=[
                    CatalogProfileSensor(key="RDI", identity="dvl_teledyne"),
                    CatalogProfileSensor(
                        key="OAS",
                        identity="dvl_teledyne",
                        extrinsics=_extrinsics(),
                    ),
                ],
            )
        ],
        vessel_profiles=[CatalogVesselProfile(key="linnaeus", vessel_name="")],
    )

    summary: CatalogSummary = summarize_catalog(catalog)
    gaps: dict[str, list[str]] = {
        gap.field_name: gap.record_keys for gap in summary.curation_gaps
    }

    assert gaps["sensor_identities.vendor"] == ["dvl_teledyne"]
    assert gaps["platform_profiles.platform_operator"] == ["sirius_2010"]
    assert gaps["platform_profiles.sensors.extrinsics"] == ["sirius_2010[RDI]"]
    assert gaps["vessel_profiles.vessel_name"] == ["linnaeus"]
    assert "platform_profiles.platform_label" not in gaps


def test_summarize_orders_gaps_by_descending_count_then_field() -> None:
    """Ordering is deterministic so repeated runs read the same."""
    catalog = DeploymentCatalog(
        sensor_identities=[
            _sensor_identity(key="dvl_teledyne", vendor=""),
            _sensor_identity(key="usbl_linkquest_transceiver", vendor=""),
        ],
        vessel_profiles=[CatalogVesselProfile(key="linnaeus", vessel_name="")],
    )

    summary: CatalogSummary = summarize_catalog(catalog)

    assert [gap.field_name for gap in summary.curation_gaps] == [
        "sensor_identities.vendor",
        "vessel_profiles.vessel_name",
    ]


def test_summarize_accepts_an_empty_catalog() -> None:
    """An empty catalog summarizes to zeros rather than failing."""
    summary: CatalogSummary = summarize_catalog(DeploymentCatalog())

    assert summary.sensor_identity_count == 0
    assert summary.coverage.deployment_count == 0
    assert not summary.platform_assignments
    assert not summary.curation_gaps


def test_run_summarize_catalog_reads_the_input(tmp_path: Path) -> None:
    """The task reads the catalog and returns the computed summary."""
    input_file: Path = tmp_path / "catalog.toml"
    write_deployment_catalog(input_file, _build_catalog())

    result: SummarizeCatalogResult = run_summarize_catalog(
        SummarizeCatalogCommand(input_file=input_file)
    )

    assert result.summary.platform_profile_count == 1
    assert result.summary.coverage.deployment_count == 2


def test_run_summarize_catalog_rejects_a_missing_input(tmp_path: Path) -> None:
    """A missing input file fails before anything is read."""
    with pytest.raises(FileNotFoundError):
        run_summarize_catalog(
            SummarizeCatalogCommand(input_file=tmp_path / "missing.toml")
        )


def test_cli_summarize_catalog_exits_zero_with_gaps(tmp_path: Path) -> None:
    """Curation gaps are output, not failure, so the command exits zero."""
    input_file: Path = tmp_path / "catalog.toml"
    write_deployment_catalog(
        input_file,
        DeploymentCatalog(
            sensor_identities=[_sensor_identity(vendor="")],
            vessel_profiles=[
                CatalogVesselProfile(key="linnaeus", vessel_name="")
            ],
        ),
    )

    runner = CliRunner()
    result: Result = runner.invoke(
        cli,
        [
            "deployment",
            "summarize-catalog",
            "--input",
            str(input_file),
            "--verbose",
        ],
    )

    assert result.exit_code == 0, result.output
