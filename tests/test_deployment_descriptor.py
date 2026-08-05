"""Tests for the deployment descriptor datatypes, IO, and file manifest."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from afft.deployment import (
    DeploymentDescriptor,
    DeploymentMetadata,
    FileDescriptorSection,
    PlatformDescriptorSection,
    PlatformIdentity,
    PlatformSensor,
    SensorCalibration,
    SensorExtrinsics,
    SystemDescriptorSection,
    TelemetryDescriptorSection,
    VesselDescriptorSection,
    VesselIdentity,
    VesselSensor,
    collect_deployment_files,
    read_deployment_descriptors,
    write_deployment_descriptors,
)
from afft.io import read_config

DEPLOYMENT_NAME: str = "qd66hv_20170525_234600_deployment_data"

DEPLOYMENT_FILES: tuple[str, ...] = (
    "messages/20170525_2346.RAW.auv",
    "messages/20170526_0000.RAW.auv",
    "messages/20170525_2346.SEABED.syscfg",
    "messages/20170525_2346.SEABED.localiser.cfg",
    "messages/20170525_2346.magnetic_variation.cfg",
    "messages/20170525_2347.SS11_snapperbank.dat.log",
    "messages/20170525_2346.CTL.auv",
    "camera_calibration/renav20170526/usyd_pool_20170118.calib",
    "camera_poses/renav20170526_stereo_pose_est.data",
    "camera_poses/renav20170526/stereo_pose_est.data",
    "usbl/log-20170525-234333.txt",
    "usbl/log-20170525-234701.txt",
)


def _build_deployment(root: Path, names: tuple[str, ...]) -> Path:
    """Builds a synthetic deployment directory tree and returns its root."""
    directory = root / DEPLOYMENT_NAME
    for name in names:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    return directory


def _build_descriptor() -> DeploymentDescriptor:
    """Builds a descriptor with every curated slot left unfilled."""
    return DeploymentDescriptor(
        deployment_label="qd66hv_20170525_234600",
        deployment_datetime=datetime(
            2017, 5, 25, 23, 46, 0, tzinfo=timezone.utc
        ),
        metadata=DeploymentMetadata(
            acfr_deployment_label="SS11_snapperbank",
            acfr_campaign_label="WA201705",
            acfr_platform_label="",
            origin_latitude=-32.0,
            origin_longitude=115.5,
            magnetic_variation=-1.5,
        ),
        files=FileDescriptorSection(
            raw_messages=["messages/20170525_2346.RAW.auv"],
            system_config=["messages/20170525_2346.SEABED.syscfg"],
        ),
        telemetry=TelemetryDescriptorSection(topics=["RDI", "VIS"]),
        platform=PlatformDescriptorSection(
            sensors=[PlatformSensor(key="RDI"), PlatformSensor(key="VIS")]
        ),
        system=SystemDescriptorSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["SYSLOG", "RAW"],
        ),
    )


def test_descriptor_round_trip(tmp_path: Path) -> None:
    descriptor = _build_descriptor()
    path = tmp_path / "deployments.toml"

    write_deployment_descriptors(path, [descriptor])

    assert read_deployment_descriptors(path) == [descriptor]


def test_descriptor_datetime_is_native_toml_datetime(tmp_path: Path) -> None:
    path = tmp_path / "deployments.toml"

    write_deployment_descriptors(path, [_build_descriptor()])

    # Unquoted, so TOML decodes it back to a datetime rather than a string.
    assert "deployment_datetime = 2017-05-25 23:46:00+00:00" in path.read_text()
    assert isinstance(
        read_config(path)["deployments"][0]["deployment_datetime"], datetime
    )


def test_unfilled_curated_slots_are_omitted(tmp_path: Path) -> None:
    path = tmp_path / "deployments.toml"

    write_deployment_descriptors(path, [_build_descriptor()])

    entry = read_config(path)["deployments"][0]
    assert entry["vessel"] == {"sensors": []}
    assert "identity" not in entry["platform"]
    assert "identity" not in entry["platform"]["sensors"][0]
    assert "extrinsics" not in entry["platform"]["sensors"][0]
    assert "calibration" not in entry["platform"]["sensors"][0]

    descriptors = read_deployment_descriptors(path)
    assert descriptors[0].vessel == VesselDescriptorSection()
    assert descriptors[0].platform.identity is None
    assert descriptors[0].platform.sensors[0].identity is None
    assert descriptors[0].platform.sensors[0].extrinsics is None
    assert descriptors[0].platform.sensors[0].calibration is None


def test_filled_curated_slots_round_trip(tmp_path: Path) -> None:
    descriptor = _build_descriptor().model_copy(
        update={
            "platform": PlatformDescriptorSection(
                identity=PlatformIdentity(
                    platform_label="AUV Sirius",
                    platform_class="SEABED",
                    platform_operator="ACFR",
                ),
                sensors=[
                    PlatformSensor(
                        key="RDI",
                        extrinsics=SensorExtrinsics(
                            locx=0.1,
                            locy=0.2,
                            locz=0.3,
                            rotx=0.0,
                            roty=0.0,
                            rotz=3.14,
                        ),
                        calibration=SensorCalibration(
                            calibration_type="pinhole",
                            parameters={"fx": 500.0, "fy": 500.0},
                        ),
                    )
                ],
            ),
        }
    )
    path = tmp_path / "deployments.toml"

    write_deployment_descriptors(path, [descriptor])

    assert read_deployment_descriptors(path) == [descriptor]


def test_filled_vessel_section_round_trip(tmp_path: Path) -> None:
    descriptor = _build_descriptor().model_copy(
        update={
            "vessel": VesselDescriptorSection(
                identity=VesselIdentity(vessel_name="RV Linnaeus"),
                sensors=[
                    VesselSensor(
                        key="USBL",
                        extrinsics=SensorExtrinsics(
                            locx=1.0,
                            locy=-0.5,
                            locz=2.5,
                            rotx=0.0,
                            roty=0.0,
                            rotz=1.57,
                        ),
                        calibration=SensorCalibration(
                            calibration_type="pinhole",
                            parameters={"fx": 500.0, "fy": 500.0},
                        ),
                    )
                ],
            ),
        }
    )
    path = tmp_path / "deployments.toml"

    write_deployment_descriptors(path, [descriptor])

    assert read_deployment_descriptors(path) == [descriptor]


def test_collect_files_assigns_every_role(tmp_path: Path) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_FILES)

    files = collect_deployment_files(directory)

    assert files.root == directory
    assert files.system_config.name == "20170525_2346.SEABED.syscfg"
    assert files.localizer_config.name == "20170525_2346.SEABED.localiser.cfg"
    assert files.magvar_config is not None
    assert files.mission_log is not None
    assert len(files.raw_messages) == 2
    assert len(files.usbl_logs) == 2
    assert len(files.camera_calibrations) == 1
    assert len(files.camera_poses) == 2


def test_collect_files_partitions_exhaustively(tmp_path: Path) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_FILES)

    files = collect_deployment_files(directory)

    assigned = [
        files.system_config,
        files.localizer_config,
        files.magvar_config,
        files.mission_log,
        *files.raw_messages,
        *files.usbl_logs,
        *files.camera_calibrations,
        *files.camera_poses,
        *files.other,
    ]
    assert len(assigned) == len(DEPLOYMENT_FILES)
    assert files.other == [directory / "messages/20170525_2346.CTL.auv"]


def test_collect_files_optional_singulars_default_to_none(
    tmp_path: Path,
) -> None:
    names = tuple(
        name
        for name in DEPLOYMENT_FILES
        if not name.endswith((".magnetic_variation.cfg", ".log"))
    )
    directory = _build_deployment(tmp_path, names)

    files = collect_deployment_files(directory)

    assert files.magvar_config is None
    assert files.mission_log is None


def test_collect_files_raises_on_missing_required_singular(
    tmp_path: Path,
) -> None:
    names = tuple(
        name for name in DEPLOYMENT_FILES if not name.endswith(".syscfg")
    )
    directory = _build_deployment(tmp_path, names)

    with pytest.raises(ValueError, match="system_config"):
        collect_deployment_files(directory)


def test_collect_files_raises_on_duplicated_required_singular(
    tmp_path: Path,
) -> None:
    directory = _build_deployment(
        tmp_path,
        DEPLOYMENT_FILES + ("messages/20170526_0000.SEABED.localiser.cfg",),
    )

    with pytest.raises(ValueError, match="localizer_config"):
        collect_deployment_files(directory)
