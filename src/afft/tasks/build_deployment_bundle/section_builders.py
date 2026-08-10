"""Orchestration writing bundle sections from an enriched descriptor and
parsed raw message logs, pairing a key with a frame and passing both to
`writer.write_frame`."""

from pathlib import Path
from typing import Any

from afft.deployment import (
    DeploymentBundleWriter,
    DeploymentDescriptor,
    DeploymentFiles,
    DeploymentIdentity,
    DeploymentProvenance,
    PlatformSensor,
    VesselSensor,
    open_deployment_bundle_writer,
)
from afft.seabed import Message, Topic

from . import (
    frame_builders,
    key_builders,
)
from .types import (
    BuildDeploymentBundleData,
    BuildDeploymentBundleDiagnostics,
    BuildDeploymentBundleResult,
)


def build_deployment_section(
    writer: DeploymentBundleWriter,
    descriptor: DeploymentDescriptor,
    files: DeploymentFiles,
) -> None:
    """Write the bundle's ``deployment/*`` frames."""
    writer.write_frame(
        key_builders.deployment_identity_key(),
        frame_builders.record_to_frame(
            DeploymentIdentity(
                deployment_label=descriptor.deployment_label,
                deployment_datetime=descriptor.deployment_datetime,
            )
        ),
        if_exists="fail",
    )
    writer.write_frame(
        key_builders.deployment_metadata_key(),
        frame_builders.record_to_frame(descriptor.metadata),
        if_exists="fail",
    )
    writer.write_frame(
        key_builders.deployment_files_key(),
        frame_builders.build_deployment_files_frame(files),
        if_exists="fail",
    )
    writer.write_frame(
        key_builders.deployment_provenance_key(),
        frame_builders.record_to_frame(
            DeploymentProvenance(deployment_key=descriptor.deployment_label)
        ),
        if_exists="fail",
    )


def build_platform_section(
    writer: DeploymentBundleWriter, descriptor: DeploymentDescriptor
) -> None:
    """Write the bundle's ``platform/*`` frames."""
    assert descriptor.platform.identity is not None
    writer.write_frame(
        key_builders.root_identity_key("platform"),
        frame_builders.record_to_frame(descriptor.platform.identity),
        if_exists="fail",
    )
    for sensor in descriptor.platform.sensors:
        _write_sensor(writer, "platform", sensor)


def build_vessel_section(
    writer: DeploymentBundleWriter, descriptor: DeploymentDescriptor
) -> None:
    """Write the bundle's ``vessel/*`` frames."""
    assert descriptor.vessel.identity is not None
    writer.write_frame(
        key_builders.root_identity_key("vessel"),
        frame_builders.record_to_frame(descriptor.vessel.identity),
        if_exists="fail",
    )
    for sensor in descriptor.vessel.sensors:
        _write_sensor(writer, "vessel", sensor)


def build_raw_telemetry_section(
    writer: DeploymentBundleWriter,
    descriptor: DeploymentDescriptor,
    message_groups: dict[Topic, list[Message[Any, Any]]],
) -> None:
    """Write the bundle's ``telemetry/raw/*`` frames, one per topic."""
    sensors: list[PlatformSensor | VesselSensor] = [
        *descriptor.platform.sensors,
        *descriptor.vessel.sensors,
    ]
    topic_to_sensor_key: dict[Topic, str] = {
        topic: sensor.key
        for sensor in sensors
        for topic in sensor.message_topics
    }

    for topic, messages in message_groups.items():
        sensor_key = topic_to_sensor_key[topic]
        writer.write_frame(
            key_builders.raw_telemetry_key(sensor_key, topic),
            frame_builders.build_raw_telemetry_frame(
                sensor_key, topic, messages
            ),
            if_exists="fail",
        )


def build_deployment_bundle(
    output_file: Path,
    data: BuildDeploymentBundleData,
    diagnostics: BuildDeploymentBundleDiagnostics,
) -> BuildDeploymentBundleResult:
    """
    Write a deployment bundle from already-parsed data.

    Arguments
    ---------
    output_file: Path to write the deployment bundle to.
    data: Descriptor, file manifest, and parsed raw messages to build from.
    diagnostics: Warnings accumulated so far, carried through to the result.

    Returns
    -------
    The build's result, including the run's diagnostics.
    """
    writer: DeploymentBundleWriter
    with open_deployment_bundle_writer(output_file) as writer:
        build_deployment_section(writer, data.descriptor, data.files)
        build_platform_section(writer, data.descriptor)
        build_vessel_section(writer, data.descriptor)
        build_raw_telemetry_section(
            writer, data.descriptor, data.message_groups
        )

    return BuildDeploymentBundleResult(
        deployment_label=data.descriptor.deployment_label,
        output_file=output_file,
        diagnostics=diagnostics,
    )


def _write_sensor(
    writer: DeploymentBundleWriter,
    root: str,
    sensor: PlatformSensor | VesselSensor,
) -> None:
    """Write a sensor's identity/message_topics/extrinsics/calibration
    frames, skipping any field that is `None`/empty."""
    if sensor.identity is not None:
        writer.write_frame(
            key_builders.sensor_identity_key(root, sensor.key),
            frame_builders.record_to_frame(sensor.identity),
            if_exists="fail",
        )
    if sensor.message_topics:
        writer.write_frame(
            key_builders.sensor_message_topics_key(root, sensor.key),
            frame_builders.message_topics_to_frame(sensor.message_topics),
            if_exists="fail",
        )
    if sensor.extrinsics is not None:
        writer.write_frame(
            key_builders.sensor_extrinsics_key(root, sensor.key),
            frame_builders.record_to_frame(sensor.extrinsics),
            if_exists="fail",
        )
    if sensor.calibration is not None:
        writer.write_frame(
            key_builders.sensor_calibration_key(root, sensor.key),
            frame_builders.sensor_calibration_to_frame(sensor.calibration),
            if_exists="fail",
        )
