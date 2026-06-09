"""Actions for Renav CLI commands."""

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config
from afft.tasks.collect_renav_stereo_poses import (
    CollectRenavStereoPosesCommand,
    run_collect_renav_stereo_poses,
)
from afft.tasks.correct_renav_camera_poses import (
    CorrectRenavCameraPosesBatchCommand,
    CorrectRenavCameraPosesCommand,
    run_correct_renav_camera_poses,
    run_correct_renav_camera_poses_batch,
)
from afft.tasks.process_renav import (
    ProcessRenavPosesBatchCommand,
    ProcessRenavPosesCommand,
    run_process_renav_poses,
    run_process_renav_poses_batch,
)
from afft.tasks.transform_camera_poses import (
    CameraVehicleExtrinsics,
    TransformCameraPosesBatchCommand,
    TransformCameraPosesCommand,
    run_transform_camera_poses,
    run_transform_camera_poses_batch,
)


def dispatch_process_renav(
    input_file: str | Path,
    output_file: str | Path,
) -> None:
    """Process a Renav stereo pose estimate file and write to CSV."""
    command = ProcessRenavPosesCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
    )
    run_process_renav_poses(command)


def dispatch_batch_process_renav(
    input_dir: str | Path,
    output_dir: str | Path,
    pattern: str = "*.txt",
) -> None:
    """Batch process Renav stereo pose estimate files in a directory."""
    command = ProcessRenavPosesBatchCommand(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        pattern=pattern,
    )
    run_process_renav_poses_batch(command)


def dispatch_collect_renav_stereo_poses(
    root_dir: str | Path,
    output_dir: str | Path,
    deployment_suffix: str = "_deployment_data",
    appendix: str = "_renav_stereo_poses.txt",
    tiebreak_margin: float = 0.03,
) -> None:
    """Collect and relabel Renav stereo pose estimate files by deployment."""
    command = CollectRenavStereoPosesCommand(
        root_dir=Path(root_dir),
        output_dir=Path(output_dir),
        deployment_suffix=deployment_suffix,
        appendix=appendix,
        tiebreak_margin=tiebreak_margin,
    )
    run_collect_renav_stereo_poses(command)


def dispatch_correct_renav_poses(
    target_file: str | Path,
    source_file: str | Path,
    output_file: str | Path,
) -> None:
    """Correct Renav camera poses with source camera pose latitude/longitude."""
    command = CorrectRenavCameraPosesCommand(
        target_file=Path(target_file),
        source_file=Path(source_file),
        output_file=Path(output_file),
    )
    run_correct_renav_camera_poses(command)


def dispatch_batch_correct_renav_poses(
    target_dir: str | Path,
    source_dir: str | Path,
    output_dir: str | Path,
    target_suffix: str = "_renav_stereo_poses.csv",
    source_suffix: str = "_cameras.csv",
) -> None:
    """Batch-correct Renav camera poses with source camera pose latitude/longitude."""
    command = CorrectRenavCameraPosesBatchCommand(
        target_dir=Path(target_dir),
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
        target_suffix=target_suffix,
        source_suffix=source_suffix,
    )
    run_correct_renav_camera_poses_batch(command)


def dispatch_transform_camera_poses(
    input_file: str | Path,
    output_file: str | Path,
    vehicle_config_file: str | Path,
) -> None:
    """Transform camera poses to vehicle reference-point poses."""
    extrinsics: CameraVehicleExtrinsics = _load_stereo_extrinsics(
        Path(vehicle_config_file)
    )
    command = TransformCameraPosesCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
    )
    run_transform_camera_poses(command, extrinsics)


def dispatch_transform_camera_poses_batch(
    input_dir: str | Path,
    output_dir: str | Path,
    vehicle_config_file: str | Path,
    input_suffix: str = "_renav_stereo_poses.csv",
    output_suffix: str = "_vehicle_poses.csv",
) -> None:
    """Batch-transform camera poses to vehicle reference-point poses."""
    extrinsics: CameraVehicleExtrinsics = _load_stereo_extrinsics(
        Path(vehicle_config_file)
    )
    command = TransformCameraPosesBatchCommand(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        input_suffix=input_suffix,
        output_suffix=output_suffix,
    )
    run_transform_camera_poses_batch(command, extrinsics)


def _load_stereo_extrinsics(
    vehicle_config_file: Path,
) -> CameraVehicleExtrinsics:
    data: dict[str, Any] = read_config(vehicle_config_file)
    stereo: dict[str, Any] = data["sensors"]["stereo"]
    return CameraVehicleExtrinsics(
        posx=stereo["posx"],
        posy=stereo["posy"],
        posz=stereo["posz"],
        rotx=stereo["rotx"],
        roty=stereo["roty"],
        rotz=stereo["rotz"],
    )
