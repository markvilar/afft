"""Actions for Renav CLI commands."""

from pathlib import Path

from afft.deployment import (
    DeploymentDescriptor,
    PlatformSensor,
    SensorExtrinsics,
    read_deployment_descriptors,
)
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

CAMERA_SENSOR_TYPE: str = "stereo_camera"


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
    descriptor_file: str | Path,
    deployment_label: str,
) -> None:
    """Transform camera poses to vehicle reference-point poses."""
    extrinsics: CameraVehicleExtrinsics = _load_camera_extrinsics(
        Path(descriptor_file), deployment_label
    )
    command = TransformCameraPosesCommand(
        input_file=Path(input_file),
        output_file=Path(output_file),
    )
    run_transform_camera_poses(command, extrinsics)


def dispatch_transform_camera_poses_batch(
    input_dir: str | Path,
    output_dir: str | Path,
    descriptor_file: str | Path,
    input_suffix: str = "_renav_stereo_poses.csv",
    output_suffix: str = "_vehicle_poses.csv",
) -> None:
    """Batch-transform camera poses to vehicle reference-point poses."""
    extrinsics: dict[str, CameraVehicleExtrinsics] = (
        _load_camera_extrinsics_by_deployment(Path(descriptor_file))
    )
    command = TransformCameraPosesBatchCommand(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        input_suffix=input_suffix,
        output_suffix=output_suffix,
    )
    run_transform_camera_poses_batch(command, extrinsics)


def _load_camera_extrinsics(
    descriptor_file: Path,
    deployment_label: str,
) -> CameraVehicleExtrinsics:
    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        descriptor_file
    )
    matches: list[DeploymentDescriptor] = [
        descriptor
        for descriptor in descriptors
        if descriptor.deployment_label == deployment_label
    ]
    if not matches:
        labels: str = ", ".join(
            sorted(descriptor.deployment_label for descriptor in descriptors)
        )
        raise KeyError(
            f"deployment {deployment_label} not in {descriptor_file};"
            f" available: {labels}"
        )
    return _camera_extrinsics(matches[0])


def _load_camera_extrinsics_by_deployment(
    descriptor_file: Path,
) -> dict[str, CameraVehicleExtrinsics]:
    """
    Resolve camera extrinsics for every deployment in a descriptors file that
    has them.

    Deployments without a usable camera pose are left out rather than raising
    here: the batch runner raises for the deployments it actually processes, so
    an unrelated unenriched entry in the file does not fail the whole run.
    """
    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        descriptor_file
    )
    resolved: dict[str, CameraVehicleExtrinsics] = {}
    for descriptor in descriptors:
        sensor: PlatformSensor | None = _find_camera_sensor(descriptor)
        if sensor is not None and sensor.extrinsics is not None:
            resolved[descriptor.deployment_label] = _camera_vehicle_extrinsics(
                sensor.extrinsics
            )
    return resolved


def _camera_extrinsics(
    descriptor: DeploymentDescriptor,
) -> CameraVehicleExtrinsics:
    """
    Resolve a deployment's stereo camera extrinsics from its platform roster.

    The task transforms the poses of a single deployment, so a descriptor
    without a usable camera pose is an error rather than something to skip.
    """
    sensor: PlatformSensor | None = _find_camera_sensor(descriptor)
    if sensor is None:
        raise KeyError(
            f"deployment {descriptor.deployment_label} has no"
            f" {CAMERA_SENSOR_TYPE} sensor in its platform roster"
        )
    if sensor.extrinsics is None:
        raise ValueError(
            f"deployment {descriptor.deployment_label} has no extrinsics for"
            f" its {CAMERA_SENSOR_TYPE} sensor"
        )
    return _camera_vehicle_extrinsics(sensor.extrinsics)


def _find_camera_sensor(
    descriptor: DeploymentDescriptor,
) -> PlatformSensor | None:
    # The roster is keyed on the mounted unit, and the vehicle flew two
    # different cameras over the years, so the camera is found by sensor type
    # rather than by key.
    for sensor in descriptor.platform.sensors:
        if sensor.identity is not None:
            if sensor.identity.type == CAMERA_SENSOR_TYPE:
                return sensor
    return None


def _camera_vehicle_extrinsics(
    extrinsics: SensorExtrinsics,
) -> CameraVehicleExtrinsics:
    # Descriptor rotations are in radians, as CameraVehicleExtrinsics expects.
    return CameraVehicleExtrinsics(
        posx=extrinsics.locx,
        posy=extrinsics.locy,
        posz=extrinsics.locz,
        rotx=extrinsics.rotx,
        roty=extrinsics.roty,
        rotz=extrinsics.rotz,
    )
