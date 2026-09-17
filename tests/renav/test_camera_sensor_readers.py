"""Tests for Renav camera sensor calibration readers."""

from pathlib import Path

import numpy as np
import pytest

from afft.renav.camera_sensor_readers import (
    read_master_camera_sensor,
    read_slave_camera_sensor,
    read_stereo_camera_rig,
)
from afft.renav.camera_sensor_types import CameraSensor, StereoCameraRig


DATA_DIR: Path = Path(__file__).parent / "data"
CALIB_PATH: Path = DATA_DIR / "stereo.calib"


def test_read_stereo_camera_rig_parses_master_intrinsics() -> None:
    rig: StereoCameraRig = read_stereo_camera_rig(CALIB_PATH)
    calibration = rig.master.calibration
    assert rig.master.image_width == 1360
    assert rig.master.image_height == 1024
    assert calibration.fx == pytest.approx(1678.489)
    assert calibration.fy == pytest.approx(1698.198)
    assert calibration.cx == pytest.approx(693.997)
    assert calibration.cy == pytest.approx(603.294)


def test_read_stereo_camera_rig_parses_master_distortion() -> None:
    calibration = read_stereo_camera_rig(CALIB_PATH).master.calibration
    assert calibration.k1 == pytest.approx(0.10974)
    assert calibration.k2 == pytest.approx(0.54105)
    assert calibration.p1 == pytest.approx(0.01731)
    assert calibration.p2 == pytest.approx(0.00385)
    assert calibration.k3 == pytest.approx(0.0)


def test_master_has_identity_pose() -> None:
    master: CameraSensor = read_stereo_camera_rig(CALIB_PATH).master
    assert master.location_in_master == (0.0, 0.0, 0.0)
    assert np.allclose(master.rotation_matrix, np.eye(3))
    assert master.is_master
    assert not master.is_slave
    assert master.master_camera_sensor is None


def test_slave_pose_and_master_reference() -> None:
    rig: StereoCameraRig = read_stereo_camera_rig(CALIB_PATH)
    slave: CameraSensor = rig.slave
    assert slave.location_in_master == pytest.approx(
        (-0.07171, 0.00020, -0.00069)
    )
    assert slave.rotation_in_master[0] == pytest.approx(
        (0.99988, 0.00561, 0.01394)
    )
    assert slave.is_slave
    assert not slave.is_master
    assert slave.master_camera_sensor == rig.master
    assert slave.master == rig.master


def test_camera_matrix_property() -> None:
    calibration = read_stereo_camera_rig(CALIB_PATH).master.calibration
    expected = np.array(
        [
            [1678.489, 0.0, 693.997],
            [0.0, 1698.198, 603.294],
            [0.0, 0.0, 1.0],
        ]
    )
    assert np.allclose(calibration.camera_matrix, expected)


def test_distortion_coefficients_property_opencv_order() -> None:
    calibration = read_stereo_camera_rig(CALIB_PATH).master.calibration
    assert np.allclose(
        calibration.distortion_coefficients,
        [0.10974, 0.54105, 0.01731, 0.00385, 0.0],
    )


def test_slave_transform_to_master() -> None:
    slave: CameraSensor = read_stereo_camera_rig(CALIB_PATH).slave
    transform = slave.transform_to_master
    assert np.allclose(transform.translation, [-0.07171, 0.00020, -0.00069])
    # scipy re-orthonormalizes the rotation, so the rounded fixture matrix is
    # only recovered to within a loose tolerance.
    assert np.allclose(
        transform.rotation.as_matrix(), slave.rotation_matrix, atol=1e-3
    )


def test_read_master_and_slave_camera_sensor() -> None:
    master: CameraSensor = read_master_camera_sensor(CALIB_PATH)
    slave: CameraSensor = read_slave_camera_sensor(CALIB_PATH)
    assert master.is_master
    assert slave.is_slave
    assert slave.master_camera_sensor == master


def test_default_keys_labels_and_color_bands() -> None:
    rig: StereoCameraRig = read_stereo_camera_rig(CALIB_PATH)
    assert (rig.master.key, rig.slave.key) == ("left", "right")
    assert (rig.master.label, rig.slave.label) == ("left", "right")
    assert rig.master.color_bands is CameraSensor.ColorBands.RGB
    assert rig.slave.color_bands is CameraSensor.ColorBands.MONO


def test_override_keys_labels_and_color_bands() -> None:
    rig: StereoCameraRig = read_stereo_camera_rig(
        CALIB_PATH,
        color_bands=(CameraSensor.ColorBands.RGB, CameraSensor.ColorBands.RGB),
        keys=("port", "starboard"),
        labels=("Port", "Starboard"),
    )
    assert (rig.master.key, rig.slave.key) == ("port", "starboard")
    assert (rig.master.label, rig.slave.label) == ("Port", "Starboard")
    assert rig.master.color_bands is CameraSensor.ColorBands.RGB
    assert rig.slave.color_bands is CameraSensor.ColorBands.RGB


def test_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        read_stereo_camera_rig(DATA_DIR / "does_not_exist.calib")


def test_camera_count_mismatch_raises(tmp_path: Path) -> None:
    path: Path = tmp_path / "bad.calib"
    path.write_text("2\n\n" + "1360 1024 " + "1.0 " * 25 + "\n")
    with pytest.raises(ValueError, match="camera count mismatch"):
        read_stereo_camera_rig(path)


def test_non_stereo_count_raises(tmp_path: Path) -> None:
    path: Path = tmp_path / "mono.calib"
    line: str = "1360 1024 " + "1.0 " * 25
    path.write_text(f"1\n\n{line}\n")
    with pytest.raises(ValueError, match="stereo rig"):
        read_stereo_camera_rig(path)


def test_malformed_camera_line_raises(tmp_path: Path) -> None:
    path: Path = tmp_path / "malformed.calib"
    path.write_text("2\n\n1360 1024 1.0\n1360 1024 1.0\n")
    with pytest.raises(ValueError, match="values per camera"):
        read_stereo_camera_rig(path)
