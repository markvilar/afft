"""Tests for the transform camera poses task and its CLI."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pymap3d
import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.cli.renav.actions import (
    _camera_extrinsics,
    _load_camera_extrinsics,
    _load_camera_extrinsics_by_deployment,
)
from afft.deployment import (
    DeploymentDescriptor,
    DeploymentMetadata,
    FileDescriptorSection,
    PlatformDescriptorSection,
    PlatformSensor,
    SensorExtrinsics,
    SensorIdentity,
    SystemDescriptorSection,
    TelemetryDescriptorSection,
    write_deployment_descriptors,
)
from afft.tasks.transform_camera_poses import (
    CameraVehicleExtrinsics,
    TransformCameraPosesBatchCommand,
    TransformCameraPosesCommand,
    run_transform_camera_poses,
    run_transform_camera_poses_batch,
)


def _displacement(
    cameras: pd.DataFrame,
    vehicles: pd.DataFrame,
    index: int = 0,
) -> tuple[float, float]:
    """
    Displacement from a camera pose to its transformed vehicle pose, in metres.

    Returns the north and east components, so the expectations below are stated
    in the vehicle body frame rather than in degrees of latitude and longitude.

    Arguments
    ---------
    cameras: Camera poses as read from the task's input file.
    vehicles: Vehicle poses as written by the task.
    index: Row to compare.

    Returns
    -------
    North and east displacement in metres.
    """
    north: float
    east: float
    north, east, _ = pymap3d.geodetic2ned(
        vehicles["latitude"].iloc[index],
        vehicles["longitude"].iloc[index],
        0.0,
        cameras["latitude"].iloc[index],
        cameras["longitude"].iloc[index],
        0.0,
    )
    return float(north), float(east)


def _build_descriptor(
    label: str,
    sensors: list[PlatformSensor],
) -> DeploymentDescriptor:
    """Builds a descriptor carrying only the fields the extrinsics lookup reads."""
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
        telemetry=TelemetryDescriptorSection(topics=[]),
        platform=PlatformDescriptorSection(sensors=sensors),
        system=SystemDescriptorSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["RAW"],
        ),
    )


def _camera_identity() -> SensorIdentity:
    """The curated identity the camera is found by."""
    return SensorIdentity(
        label="AVT Prosilica GC1380 stereo camera",
        vendor="AVT",
        product="Prosilica GC1380",
        type="stereo_camera",
    )


def _dvl_sensor() -> PlatformSensor:
    """A roster entry that is not a camera."""
    return PlatformSensor(
        key="dvl_teledyne_navigator",
        identity=SensorIdentity(
            label="Teledyne RDI Work Horse Navigator DVL",
            vendor="Teledyne RDI",
            product="Work Horse Navigator",
            type="dvl",
        ),
    )


def _camera_sensor(posx: float = 0.82) -> PlatformSensor:
    """A camera sensor carrying the catalog's curated stereo camera pose."""
    return PlatformSensor(
        key="camera_avt_prosilica",
        identity=_camera_identity(),
        extrinsics=SensorExtrinsics(
            locx=posx,
            locy=-0.035,
            locz=0.0,
            rotx=-0.0373,
            roty=-0.0065,
            rotz=1.5488,
        ),
    )


def _write_descriptors(
    path: Path,
    descriptors: list[DeploymentDescriptor],
) -> Path:
    write_deployment_descriptors(path, descriptors)
    return path


def _write_poses(
    path: Path,
    latitude: float = -28.8,
    longitude: float = 113.9,
    heading: float = 0.0,
    total: int = 3,
) -> Path:
    """Writes a camera pose CSV with a passthrough column."""
    frame = pd.DataFrame(
        {
            "timestamp": [float(index) for index in range(total)],
            "latitude": [latitude] * total,
            "longitude": [longitude] * total,
            "heading": [heading] * total,
            "pitch": [0.0] * total,
            "roll": [0.0] * total,
        }
    )
    frame.to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------------------
# Extrinsics resolution
# --------------------------------------------------------------------------------------


def test_extrinsics_resolve_from_descriptor(tmp_path: Path) -> None:
    """Descriptor values pass through in radians, unconverted."""
    path = _write_descriptors(
        tmp_path / "descriptors.toml",
        [_build_descriptor("qdch0ftq_20100428_020202", [_camera_sensor()])],
    )

    extrinsics = _load_camera_extrinsics(path, "qdch0ftq_20100428_020202")

    assert extrinsics == CameraVehicleExtrinsics(
        posx=0.82,
        posy=-0.035,
        posz=0.0,
        rotx=-0.0373,
        roty=-0.0065,
        rotz=1.5488,
    )


def test_extrinsics_lookup_rejects_unknown_deployment(tmp_path: Path) -> None:
    path = _write_descriptors(
        tmp_path / "descriptors.toml",
        [_build_descriptor("qdch0ftq_20100428_020202", [_camera_sensor()])],
    )

    with pytest.raises(KeyError, match="qd61g27j_20100421_022145"):
        _load_camera_extrinsics(path, "qd61g27j_20100421_022145")


def test_extrinsics_lookup_names_available_deployments(
    tmp_path: Path,
) -> None:
    path = _write_descriptors(
        tmp_path / "descriptors.toml",
        [_build_descriptor("qdch0ftq_20100428_020202", [_camera_sensor()])],
    )

    with pytest.raises(KeyError, match="available: qdch0ftq_20100428_020202"):
        _load_camera_extrinsics(path, "absent")


def test_extrinsics_rejects_roster_without_camera() -> None:
    descriptor = _build_descriptor("qdch0ftq_20100428_020202", [_dvl_sensor()])

    with pytest.raises(KeyError, match="no stereo_camera sensor"):
        _camera_extrinsics(descriptor)


def test_extrinsics_rejects_camera_without_a_pose() -> None:
    """The common case: a curated camera the catalog has no pose for."""
    descriptor = _build_descriptor(
        "qdch0ftq_20100428_020202",
        [
            PlatformSensor(
                key="camera_avt_prosilica", identity=_camera_identity()
            )
        ],
    )

    with pytest.raises(ValueError, match="no extrinsics"):
        _camera_extrinsics(descriptor)


def test_extrinsics_resolve_per_deployment(tmp_path: Path) -> None:
    path = _write_descriptors(
        tmp_path / "descriptors.toml",
        [
            _build_descriptor(
                "qdch0ftq_20100428_020202", [_camera_sensor(posx=0.82)]
            ),
            _build_descriptor(
                "qd61g27j_20100421_022145", [_camera_sensor(posx=1.50)]
            ),
        ],
    )

    extrinsics = _load_camera_extrinsics_by_deployment(path)

    assert set(extrinsics) == {
        "qdch0ftq_20100428_020202",
        "qd61g27j_20100421_022145",
    }
    assert extrinsics["qdch0ftq_20100428_020202"].posx == 0.82
    assert extrinsics["qd61g27j_20100421_022145"].posx == 1.50


def test_extrinsics_skip_unenriched_deployments(tmp_path: Path) -> None:
    """An unenriched entry is left out rather than failing the whole file."""
    path = _write_descriptors(
        tmp_path / "descriptors.toml",
        [
            _build_descriptor("qdch0ftq_20100428_020202", [_camera_sensor()]),
            _build_descriptor(
                "qd61g27j_20100421_022145",
                [
                    PlatformSensor(
                        key="camera_avt_prosilica",
                        identity=_camera_identity(),
                    )
                ],
            ),
            _build_descriptor("qdch0ftq_20110415_020103", [_dvl_sensor()]),
        ],
    )

    extrinsics = _load_camera_extrinsics_by_deployment(path)

    assert set(extrinsics) == {"qdch0ftq_20100428_020202"}


# --------------------------------------------------------------------------------------
# Single-deployment runner
# --------------------------------------------------------------------------------------


def test_transform_shifts_pose_against_heading(tmp_path: Path) -> None:
    """A north-facing camera 10 m forward puts the vehicle 10 m south of it."""
    input_file = _write_poses(tmp_path / "poses.csv", heading=0.0, total=1)
    output_file = tmp_path / "vehicle.csv"

    run_transform_camera_poses(
        TransformCameraPosesCommand(
            input_file=input_file, output_file=output_file
        ),
        CameraVehicleExtrinsics(posx=10.0),
    )

    north, east = _displacement(
        pd.read_csv(input_file), pd.read_csv(output_file)
    )
    assert north == pytest.approx(-10.0, abs=1e-6)
    assert east == pytest.approx(0.0, abs=1e-6)


def test_transform_shifts_pose_with_heading(tmp_path: Path) -> None:
    """Facing east, the same forward offset puts the vehicle 10 m west."""
    input_file = _write_poses(tmp_path / "poses.csv", heading=90.0, total=1)
    output_file = tmp_path / "vehicle.csv"

    run_transform_camera_poses(
        TransformCameraPosesCommand(
            input_file=input_file, output_file=output_file
        ),
        CameraVehicleExtrinsics(posx=10.0),
    )

    north, east = _displacement(
        pd.read_csv(input_file), pd.read_csv(output_file)
    )
    assert north == pytest.approx(0.0, abs=1e-6)
    assert east == pytest.approx(-10.0, abs=1e-6)


def test_transform_with_zero_extrinsics_is_identity(tmp_path: Path) -> None:
    input_file = _write_poses(
        tmp_path / "poses.csv", latitude=-28.8, longitude=113.9
    )
    output_file = tmp_path / "vehicle.csv"

    run_transform_camera_poses(
        TransformCameraPosesCommand(
            input_file=input_file, output_file=output_file
        ),
        CameraVehicleExtrinsics(),
    )

    cameras = pd.read_csv(input_file)
    vehicles = pd.read_csv(output_file)
    assert np.allclose(vehicles["latitude"], cameras["latitude"])
    assert np.allclose(vehicles["longitude"], cameras["longitude"])


def test_transform_passes_other_columns_through(tmp_path: Path) -> None:
    input_file = _write_poses(tmp_path / "poses.csv", heading=45.0)
    output_file = tmp_path / "vehicle.csv"

    result = run_transform_camera_poses(
        TransformCameraPosesCommand(
            input_file=input_file, output_file=output_file
        ),
        CameraVehicleExtrinsics(posx=0.82, posy=-0.035),
    )

    cameras = pd.read_csv(input_file)
    vehicles = pd.read_csv(output_file)
    assert result.total == len(cameras)
    assert list(vehicles.columns) == list(cameras.columns)
    for column in ["timestamp", "heading", "pitch", "roll"]:
        assert np.allclose(vehicles[column], cameras[column])


def test_transform_rejects_missing_input(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="input file"):
        run_transform_camera_poses(
            TransformCameraPosesCommand(
                input_file=tmp_path / "absent.csv",
                output_file=tmp_path / "vehicle.csv",
            ),
            CameraVehicleExtrinsics(),
        )


def test_transform_rejects_missing_output_directory(tmp_path: Path) -> None:
    input_file = _write_poses(tmp_path / "poses.csv")

    with pytest.raises(FileNotFoundError, match="output directory"):
        run_transform_camera_poses(
            TransformCameraPosesCommand(
                input_file=input_file,
                output_file=tmp_path / "absent" / "vehicle.csv",
            ),
            CameraVehicleExtrinsics(),
        )


def test_transform_rejects_output_equal_to_input(tmp_path: Path) -> None:
    input_file = _write_poses(tmp_path / "poses.csv")

    with pytest.raises(ValueError, match="must differ"):
        run_transform_camera_poses(
            TransformCameraPosesCommand(
                input_file=input_file, output_file=input_file
            ),
            CameraVehicleExtrinsics(),
        )


# --------------------------------------------------------------------------------------
# Batch runner
# --------------------------------------------------------------------------------------


def test_batch_applies_extrinsics_per_deployment(tmp_path: Path) -> None:
    """Each deployment is transformed with its own geometry, not a shared one."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    _write_poses(input_dir / "first_renav_stereo_poses.csv", total=1)
    _write_poses(input_dir / "second_renav_stereo_poses.csv", total=1)

    run_transform_camera_poses_batch(
        TransformCameraPosesBatchCommand(
            input_dir=input_dir, output_dir=output_dir
        ),
        {
            "first": CameraVehicleExtrinsics(posx=10.0),
            "second": CameraVehicleExtrinsics(posx=20.0),
        },
    )

    first_north, _ = _displacement(
        pd.read_csv(input_dir / "first_renav_stereo_poses.csv"),
        pd.read_csv(output_dir / "first_platform_poses.csv"),
    )
    second_north, _ = _displacement(
        pd.read_csv(input_dir / "second_renav_stereo_poses.csv"),
        pd.read_csv(output_dir / "second_platform_poses.csv"),
    )
    assert first_north == pytest.approx(-10.0, abs=1e-6)
    assert second_north == pytest.approx(-20.0, abs=1e-6)


def test_batch_reports_counts_per_deployment(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    _write_poses(input_dir / "first_renav_stereo_poses.csv", total=3)
    _write_poses(input_dir / "second_renav_stereo_poses.csv", total=5)

    result = run_transform_camera_poses_batch(
        TransformCameraPosesBatchCommand(
            input_dir=input_dir, output_dir=output_dir
        ),
        {
            "first": CameraVehicleExtrinsics(),
            "second": CameraVehicleExtrinsics(),
        },
    )

    assert {
        label: counts.total for label, counts in result.results.items()
    } == {"first": 3, "second": 5}


def test_batch_rejects_deployment_without_extrinsics(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    _write_poses(input_dir / "first_renav_stereo_poses.csv")

    with pytest.raises(KeyError, match="first"):
        run_transform_camera_poses_batch(
            TransformCameraPosesBatchCommand(
                input_dir=input_dir, output_dir=output_dir
            ),
            {"second": CameraVehicleExtrinsics()},
        )


def test_batch_rejects_directory_without_matches(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    _write_poses(input_dir / "unrelated.csv")

    with pytest.raises(FileNotFoundError, match="no files ending in"):
        run_transform_camera_poses_batch(
            TransformCameraPosesBatchCommand(
                input_dir=input_dir, output_dir=output_dir
            ),
            {},
        )


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def test_cli_transform_poses_uses_descriptor_extrinsics(
    tmp_path: Path,
) -> None:
    descriptor_file = _write_descriptors(
        tmp_path / "descriptors.toml",
        [
            _build_descriptor(
                "qdch0ftq_20100428_020202", [_camera_sensor(posx=10.0)]
            )
        ],
    )
    input_file = _write_poses(tmp_path / "poses.csv", total=1)
    output_file = tmp_path / "vehicle.csv"

    result: Result = CliRunner().invoke(
        cli,
        [
            "renav",
            "transform-poses",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--descriptors",
            str(descriptor_file),
            "--deployment",
            "qdch0ftq_20100428_020202",
        ],
    )

    assert result.exit_code == 0, result.output
    north, _ = _displacement(pd.read_csv(input_file), pd.read_csv(output_file))
    assert north == pytest.approx(-10.0, abs=1e-6)


def test_cli_transform_poses_fails_on_unknown_deployment(
    tmp_path: Path,
) -> None:
    descriptor_file = _write_descriptors(
        tmp_path / "descriptors.toml",
        [_build_descriptor("qdch0ftq_20100428_020202", [_camera_sensor()])],
    )
    input_file = _write_poses(tmp_path / "poses.csv")

    result: Result = CliRunner().invoke(
        cli,
        [
            "renav",
            "transform-poses",
            "--input",
            str(input_file),
            "--output",
            str(tmp_path / "vehicle.csv"),
            "--descriptors",
            str(descriptor_file),
            "--deployment",
            "absent",
        ],
    )

    assert result.exit_code != 0
    assert "qdch0ftq_20100428_020202" in str(result.exception)


def test_cli_batch_transform_poses_uses_descriptor_extrinsics(
    tmp_path: Path,
) -> None:
    descriptor_file = _write_descriptors(
        tmp_path / "descriptors.toml",
        [_build_descriptor("first", [_camera_sensor(posx=10.0)])],
    )
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    _write_poses(input_dir / "first_renav_stereo_poses.csv", total=1)

    result: Result = CliRunner().invoke(
        cli,
        [
            "renav",
            "batch-transform-poses",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--descriptors",
            str(descriptor_file),
        ],
    )

    assert result.exit_code == 0, result.output
    north, _ = _displacement(
        pd.read_csv(input_dir / "first_renav_stereo_poses.csv"),
        pd.read_csv(output_dir / "first_platform_poses.csv"),
    )
    assert north == pytest.approx(-10.0, abs=1e-6)
