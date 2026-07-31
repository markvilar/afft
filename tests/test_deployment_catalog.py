"""Tests for the curated deployment catalog datatypes and IO."""

from pathlib import Path

import pytest

from pydantic import ValidationError

from afft.deployment import (
    CatalogDeploymentPlatform,
    CatalogDeploymentVessel,
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensor,
    CatalogSensorExtrinsics,
    CatalogVesselProfile,
    DeploymentCatalog,
    read_deployment_catalog,
    write_deployment_catalog,
)
from afft.io import read_config

DVL_SENSOR: CatalogSensor = CatalogSensor(
    key="dvl_teledyne",
    label="Teledyne RDI Work Horse Navigator DVL",
    vendor="Teledyne RDI",
    product="Work Horse Navigator",
    type="dvl",
)
USBL_SENSOR: CatalogSensor = CatalogSensor(
    key="usbl_linkquest",
    label="LinkQuest TrackLink 1500HA USBL",
    vendor="LinkQuest",
    product="TrackLink 1500HA",
    type="usbl",
)


def _build_catalog() -> DeploymentCatalog:
    """Builds a catalog covering one platform and one vessel profile."""
    return DeploymentCatalog(
        sensors=[DVL_SENSOR, USBL_SENSOR],
        platform_profiles=[
            CatalogPlatformProfile(
                key="2010_auv_sirius",
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="ACFR",
                sensors=[
                    CatalogProfileSensor(
                        key="RDI",
                        identity="dvl_teledyne",
                        extrinsics=CatalogSensorExtrinsics(
                            locx=0.0,
                            locy=0.0,
                            locz=0.0,
                            rotx=0.0,
                            roty=3.1416,
                            rotz=-1.5708,
                        ),
                    ),
                    CatalogProfileSensor(
                        key="LQMODEM", identity="usbl_linkquest"
                    ),
                ],
            )
        ],
        vessel_profiles=[
            CatalogVesselProfile(
                key="201004_rv_linnaeus",
                vessel_name="RV Linnaeus",
                sensors=[
                    CatalogProfileSensor(
                        key="USBL",
                        identity="usbl_linkquest",
                        extrinsics=CatalogSensorExtrinsics(
                            locx=-5.715,
                            locy=-1.258,
                            locz=1.352,
                            rotx=0.3316,
                            roty=0.0,
                            rotz=0.3138,
                        ),
                    )
                ],
            )
        ],
        deployment_platforms=[
            CatalogDeploymentPlatform(
                deployment_label="qdch0ftq_20100428_020202",
                platform_profile="2010_auv_sirius",
            )
        ],
        deployment_vessels=[
            CatalogDeploymentVessel(
                deployment_label="qdch0ftq_20100428_020202",
                vessel_profile="201004_rv_linnaeus",
            )
        ],
    )


def test_catalog_round_trip(tmp_path: Path) -> None:
    catalog = _build_catalog()
    path = tmp_path / "catalog.toml"

    write_deployment_catalog(path, catalog)

    assert read_deployment_catalog(path) == catalog


def test_absent_extrinsics_are_omitted(tmp_path: Path) -> None:
    path = tmp_path / "catalog.toml"

    write_deployment_catalog(path, _build_catalog())

    sensors = read_config(path)["platform_profiles"][0]["sensors"]
    assert "extrinsics" in sensors[0]
    assert "extrinsics" not in sensors[1]
    assert (
        read_deployment_catalog(path).platform_profiles[0].sensors[1].extrinsics
        is None
    )


def test_rotations_carry_degree_comments(tmp_path: Path) -> None:
    path = tmp_path / "catalog.toml"

    write_deployment_catalog(path, _build_catalog())

    assert "# rotation in degrees: 0.000, 180.000, -90.000" in path.read_text()


def test_mapping_tables_are_written_sorted_by_deployment_label(
    tmp_path: Path,
) -> None:
    catalog = _build_catalog()
    unsorted = DeploymentCatalog(
        sensors=catalog.sensors,
        platform_profiles=catalog.platform_profiles,
        vessel_profiles=catalog.vessel_profiles,
        deployment_platforms=[
            CatalogDeploymentPlatform(
                deployment_label="r7jjskxq_20101023_210332",
                platform_profile="2010_auv_sirius",
            ),
            *catalog.deployment_platforms,
        ],
        deployment_vessels=[
            CatalogDeploymentVessel(
                deployment_label="r7jjskxq_20101023_210332",
                vessel_profile="201004_rv_linnaeus",
            ),
            *catalog.deployment_vessels,
        ],
    )
    path = tmp_path / "catalog.toml"

    write_deployment_catalog(path, unsorted)

    written = read_deployment_catalog(path)
    assert [
        entry.deployment_label for entry in written.deployment_platforms
    ] == ["qdch0ftq_20100428_020202", "r7jjskxq_20101023_210332"]
    assert [entry.deployment_label for entry in written.deployment_vessels] == [
        "qdch0ftq_20100428_020202",
        "r7jjskxq_20101023_210332",
    ]


def test_empty_catalog_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "catalog.toml"

    write_deployment_catalog(path, DeploymentCatalog())

    assert path.read_text() == ""
    assert read_deployment_catalog(path) == DeploymentCatalog()


def test_duplicate_sensor_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate key in sensors"):
        DeploymentCatalog(sensors=[DVL_SENSOR, DVL_SENSOR])


def test_duplicate_platform_profile_key_is_rejected() -> None:
    profile = CatalogPlatformProfile(
        key="2010_auv_sirius",
        platform_label="AUV Sirius",
        platform_class="SEABED",
        platform_operator="ACFR",
    )
    with pytest.raises(
        ValidationError, match="duplicate key in platform_profiles"
    ):
        DeploymentCatalog(platform_profiles=[profile, profile])


def test_duplicate_vessel_profile_key_is_rejected() -> None:
    profile = CatalogVesselProfile(
        key="201004_rv_linnaeus", vessel_name="RV Linnaeus"
    )
    with pytest.raises(
        ValidationError, match="duplicate key in vessel_profiles"
    ):
        DeploymentCatalog(vessel_profiles=[profile, profile])


def test_two_platform_assignments_for_one_deployment_are_rejected() -> None:
    catalog = _build_catalog()
    with pytest.raises(
        ValidationError, match="duplicate key in deployment_platforms"
    ):
        DeploymentCatalog(
            sensors=catalog.sensors,
            platform_profiles=catalog.platform_profiles,
            deployment_platforms=[
                *catalog.deployment_platforms,
                *catalog.deployment_platforms,
            ],
        )


def test_two_vessel_assignments_for_one_deployment_are_rejected() -> None:
    catalog = _build_catalog()
    with pytest.raises(
        ValidationError, match="duplicate key in deployment_vessels"
    ):
        DeploymentCatalog(
            sensors=catalog.sensors,
            vessel_profiles=catalog.vessel_profiles,
            deployment_vessels=[
                *catalog.deployment_vessels,
                *catalog.deployment_vessels,
            ],
        )


def test_unknown_sensor_identity_is_rejected() -> None:
    with pytest.raises(
        ValidationError, match="unknown sensor identity: 'dvl_teledyne'"
    ):
        DeploymentCatalog(
            platform_profiles=[
                CatalogPlatformProfile(
                    key="2010_auv_sirius",
                    platform_label="AUV Sirius",
                    platform_class="SEABED",
                    platform_operator="ACFR",
                    sensors=[
                        CatalogProfileSensor(key="RDI", identity="dvl_teledyne")
                    ],
                )
            ]
        )


def test_unknown_platform_profile_reference_is_rejected() -> None:
    with pytest.raises(
        ValidationError, match="unknown platform profile: '2010_auv_sirius'"
    ):
        DeploymentCatalog(
            deployment_platforms=[
                CatalogDeploymentPlatform(
                    deployment_label="qdch0ftq_20100428_020202",
                    platform_profile="2010_auv_sirius",
                )
            ]
        )


def test_unknown_vessel_profile_reference_is_rejected() -> None:
    with pytest.raises(
        ValidationError, match="unknown vessel profile: '201004_rv_linnaeus'"
    ):
        DeploymentCatalog(
            deployment_vessels=[
                CatalogDeploymentVessel(
                    deployment_label="qdch0ftq_20100428_020202",
                    vessel_profile="201004_rv_linnaeus",
                )
            ]
        )
