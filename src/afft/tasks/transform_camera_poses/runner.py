"""Runner for the transform camera poses task."""

from pathlib import Path

import numpy as np
import pandas as pd
import pymap3d
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation
from tqdm.auto import tqdm

from afft.utils.log import logger

from .types import (
    CameraVehicleExtrinsics,
    TransformCameraPosesBatchCommand,
    TransformCameraPosesBatchResult,
    TransformCameraPosesCommand,
    TransformCameraPosesConfig,
    TransformCameraPosesResult,
)


def run_transform_camera_poses(
    command: TransformCameraPosesCommand,
    extrinsics: CameraVehicleExtrinsics,
    config: TransformCameraPosesConfig = TransformCameraPosesConfig(),
) -> TransformCameraPosesResult:
    """
    Apply camera-to-vehicle extrinsics to shift camera poses to the vehicle
    reference point.

    Reads a camera pose CSV, applies the camera position offset expressed in
    the vehicle body frame, and writes the resulting vehicle poses to a new
    CSV. All columns except latitude and longitude are passed through
    unchanged.

    Arguments
    ---------
    command: Task I/O configuration.
    extrinsics: Camera position in the vehicle body frame.
    config: Column label configuration.

    Returns
    -------
    Number of vehicle poses written to the output file.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )
    if command.output_file.resolve() == command.input_file.resolve():
        raise ValueError(
            f"output file must differ from input file: {command.input_file}"
        )

    cameras: pd.DataFrame = pd.read_csv(command.input_file)
    vehicles: pd.DataFrame = _apply_extrinsics(cameras, extrinsics, config)
    vehicles.to_csv(command.output_file, index=False)

    result = TransformCameraPosesResult(total=len(vehicles))
    logger.info(
        f"{command.input_file.name}: {result.total} pose(s)"
        f" → {command.output_file}"
    )
    return result


def run_transform_camera_poses_batch(
    command: TransformCameraPosesBatchCommand,
    extrinsics: CameraVehicleExtrinsics,
    config: TransformCameraPosesConfig = TransformCameraPosesConfig(),
) -> TransformCameraPosesBatchResult:
    """
    Apply camera-to-vehicle extrinsics to a directory of camera pose CSVs.

    For each CSV in ``input_dir`` whose filename ends with ``input_suffix``,
    the deployment label is extracted and the vehicle poses are written to
    ``output_dir`` as ``{label}{output_suffix}``.

    Arguments
    ---------
    command: Task I/O configuration.
    extrinsics: Camera position in the vehicle body frame.
    config: Column label configuration.

    Returns
    -------
    Per-deployment pose counts keyed by deployment label.
    """
    if not command.input_dir.exists():
        raise FileNotFoundError(
            f"input directory does not exist: {command.input_dir}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )
    if command.output_dir.resolve() == command.input_dir.resolve():
        raise ValueError(
            f"output directory must differ from input directory:"
            f" {command.input_dir}"
        )

    input_files: list[Path] = sorted(
        path
        for path in command.input_dir.iterdir()
        if path.is_file() and path.name.endswith(command.input_suffix)
    )
    if not input_files:
        raise FileNotFoundError(
            f"no files ending in {command.input_suffix!r}"
            f" found in {command.input_dir}"
        )

    results: dict[str, TransformCameraPosesResult] = {}

    for input_file in tqdm(
        input_files, desc="Transforming camera poses", unit="file"
    ):
        label: str = input_file.name.removesuffix(command.input_suffix)
        output_file: Path = (
            command.output_dir / f"{label}{command.output_suffix}"
        )

        cameras: pd.DataFrame = pd.read_csv(input_file)
        vehicles: pd.DataFrame = _apply_extrinsics(cameras, extrinsics, config)
        vehicles.to_csv(output_file, index=False)

        results[label] = TransformCameraPosesResult(total=len(vehicles))

    batch_result = TransformCameraPosesBatchResult(results=results)

    for label, result in batch_result.results.items():
        logger.info(f"  {label}: {result.total} pose(s)")

    return batch_result


def _apply_extrinsics(
    cameras: pd.DataFrame,
    extrinsics: CameraVehicleExtrinsics,
    config: TransformCameraPosesConfig,
) -> pd.DataFrame:
    headings: NDArray[np.float64] = cameras[config.heading_column].to_numpy(
        dtype=np.float64
    )
    pitches: NDArray[np.float64] = cameras[config.pitch_column].to_numpy(
        dtype=np.float64
    )
    rolls: NDArray[np.float64] = cameras[config.roll_column].to_numpy(
        dtype=np.float64
    )

    rotation: Rotation = Rotation.from_euler(
        "ZYX",
        np.column_stack([headings, pitches, rolls]),
        degrees=True,
    )

    # Camera is at [posx, posy, posz] in vehicle frame (SNAME: x=forward,
    # y=starboard, z=down), which is aligned with NED, so no sign conversion
    # is needed. Vehicle origin is at the negative offset from the camera.
    camera_in_vehicle: NDArray[np.float64] = np.array(
        [extrinsics.posx, extrinsics.posy, extrinsics.posz], dtype=np.float64
    )
    delta_ned: NDArray[np.float64] = rotation.apply(-camera_in_vehicle)

    lat_camera: NDArray[np.float64] = cameras[config.latitude_column].to_numpy(
        dtype=np.float64
    )
    lon_camera: NDArray[np.float64] = cameras[config.longitude_column].to_numpy(
        dtype=np.float64
    )

    lat_vehicle: NDArray[np.float64]
    lon_vehicle: NDArray[np.float64]
    lat_vehicle, lon_vehicle, _ = pymap3d.ned2geodetic(
        delta_ned[:, 0],
        delta_ned[:, 1],
        delta_ned[:, 2],
        lat_camera,
        lon_camera,
        np.zeros(len(cameras), dtype=np.float64),
    )

    vehicles: pd.DataFrame = cameras.copy()
    vehicles[config.latitude_column] = lat_vehicle
    vehicles[config.longitude_column] = lon_vehicle
    return vehicles
