"""Readers for Renav camera sensor calibration files (``*.calib``)."""

from pathlib import Path

from afft.renav.camera_sensor_types import (
    CameraCalibration,
    CameraSensor,
    Mat3,
    StereoCameraRig,
    Vec3,
)


VALUES_PER_CAMERA: int = 27
STEREO_CAMERA_COUNT: int = 2


def _parse_camera(
    values: list[float],
    key: str,
    label: str,
    color_bands: CameraSensor.ColorBands,
    master_camera_sensor: CameraSensor | None,
) -> CameraSensor:
    """
    Build a CameraSensor from a single camera line's 27 values.

    Arguments
    ---------
    values: The 27 whitespace-separated values of a camera line.
    key: Sensor key.
    label: Sensor label.
    color_bands: Color bands captured by the sensor.
    master_camera_sensor: The master sensor, or None when this is the master.

    Returns
    -------
    A CameraSensor with its intrinsic calibration and extrinsics.
    """
    image_width: int = int(values[0])
    image_height: int = int(values[1])

    intrinsics: list[float] = values[2:11]
    distortion: list[float] = values[11:15]
    rotation: list[float] = values[15:24]
    translation: list[float] = values[24:27]

    calibration: CameraCalibration = CameraCalibration(
        image_width=image_width,
        image_height=image_height,
        fx=intrinsics[0],
        fy=intrinsics[4],
        cx=intrinsics[2],
        cy=intrinsics[5],
        k1=distortion[0],
        k2=distortion[1],
        k3=0.0,
        p1=distortion[2],
        p2=distortion[3],
    )

    rotation_in_master: Mat3 = (
        (rotation[0], rotation[1], rotation[2]),
        (rotation[3], rotation[4], rotation[5]),
        (rotation[6], rotation[7], rotation[8]),
    )
    location_in_master: Vec3 = (translation[0], translation[1], translation[2])

    return CameraSensor(
        key=key,
        label=label,
        image_width=image_width,
        image_height=image_height,
        color_bands=color_bands,
        calibration=calibration,
        location_in_master=location_in_master,
        rotation_in_master=rotation_in_master,
        master_camera_sensor=master_camera_sensor,
    )


def _read_calibration(
    path: Path,
    *,
    color_bands: tuple[CameraSensor.ColorBands, CameraSensor.ColorBands] = (
        CameraSensor.ColorBands.RGB,
        CameraSensor.ColorBands.MONO,
    ),
    keys: tuple[str, str] = ("left", "right"),
    labels: tuple[str, str] = ("left", "right"),
) -> StereoCameraRig:
    """
    Parse a Renav ``*.calib`` file into a StereoCameraRig.

    The file has a camera count on the first line, a blank line, then one line
    of 27 whitespace-separated values per camera. Camera 0 becomes the master
    (identity extrinsics) and camera 1 the slave (extrinsics relative to the
    master).

    Arguments
    ---------
    path: Path to the Renav ``.calib`` file.
    color_bands: Per-sensor color bands as (master, slave).
    keys: Per-sensor keys as (master, slave).
    labels: Per-sensor labels as (master, slave).

    Returns
    -------
    A StereoCameraRig with its master and slave camera sensors.
    """
    if not path.exists():
        raise FileNotFoundError(f"file does not exist: {path}")

    lines: list[str] = [
        line.strip() for line in path.read_text().splitlines() if line.strip()
    ]

    if not lines:
        raise ValueError(f"empty calibration file: {path}")

    declared_count: int = int(lines[0])
    camera_lines: list[str] = lines[1:]

    if len(camera_lines) != declared_count:
        raise ValueError(
            f"camera count mismatch: declared {declared_count}, "
            f"found {len(camera_lines)}"
        )

    if declared_count != STEREO_CAMERA_COUNT:
        raise ValueError(
            f"expected {STEREO_CAMERA_COUNT} cameras for a stereo rig, "
            f"found {declared_count}"
        )

    camera_values: list[list[float]] = []
    for camera_line in camera_lines:
        values: list[float] = [float(token) for token in camera_line.split()]
        if len(values) != VALUES_PER_CAMERA:
            raise ValueError(
                f"expected {VALUES_PER_CAMERA} values per camera, "
                f"found {len(values)}"
            )
        camera_values.append(values)

    master: CameraSensor = _parse_camera(
        camera_values[0],
        key=keys[0],
        label=labels[0],
        color_bands=color_bands[0],
        master_camera_sensor=None,
    )
    slave: CameraSensor = _parse_camera(
        camera_values[1],
        key=keys[1],
        label=labels[1],
        color_bands=color_bands[1],
        master_camera_sensor=master,
    )

    return StereoCameraRig(master=master, slave=slave)


def read_stereo_camera_rig(
    path: Path,
    *,
    color_bands: tuple[CameraSensor.ColorBands, CameraSensor.ColorBands] = (
        CameraSensor.ColorBands.RGB,
        CameraSensor.ColorBands.MONO,
    ),
    keys: tuple[str, str] = ("left", "right"),
    labels: tuple[str, str] = ("left", "right"),
) -> StereoCameraRig:
    """
    Read a Renav ``*.calib`` file into a StereoCameraRig.

    Arguments
    ---------
    path: Path to the Renav ``.calib`` file.
    color_bands: Per-sensor color bands as (master, slave).
    keys: Per-sensor keys as (master, slave).
    labels: Per-sensor labels as (master, slave).

    Returns
    -------
    A StereoCameraRig with its master and slave camera sensors.
    """
    return _read_calibration(
        path, color_bands=color_bands, keys=keys, labels=labels
    )


def read_master_camera_sensor(
    path: Path,
    *,
    color_bands: tuple[CameraSensor.ColorBands, CameraSensor.ColorBands] = (
        CameraSensor.ColorBands.RGB,
        CameraSensor.ColorBands.MONO,
    ),
    keys: tuple[str, str] = ("left", "right"),
    labels: tuple[str, str] = ("left", "right"),
) -> CameraSensor:
    """
    Read the master camera sensor from a Renav ``*.calib`` file.

    Arguments
    ---------
    path: Path to the Renav ``.calib`` file.
    color_bands: Per-sensor color bands as (master, slave).
    keys: Per-sensor keys as (master, slave).
    labels: Per-sensor labels as (master, slave).

    Returns
    -------
    The master CameraSensor.
    """
    return _read_calibration(
        path, color_bands=color_bands, keys=keys, labels=labels
    ).master


def read_slave_camera_sensor(
    path: Path,
    *,
    color_bands: tuple[CameraSensor.ColorBands, CameraSensor.ColorBands] = (
        CameraSensor.ColorBands.RGB,
        CameraSensor.ColorBands.MONO,
    ),
    keys: tuple[str, str] = ("left", "right"),
    labels: tuple[str, str] = ("left", "right"),
) -> CameraSensor:
    """
    Read the slave camera sensor from a Renav ``*.calib`` file.

    Arguments
    ---------
    path: Path to the Renav ``.calib`` file.
    color_bands: Per-sensor color bands as (master, slave).
    keys: Per-sensor keys as (master, slave).
    labels: Per-sensor labels as (master, slave).

    Returns
    -------
    The slave CameraSensor, carrying its master via ``master_camera_sensor``.
    """
    return _read_calibration(
        path, color_bands=color_bands, keys=keys, labels=labels
    ).slave
