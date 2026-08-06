"""Builders writing bundle sections from an enriched descriptor and parsed
raw message logs."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from afft.deployment import (
    DeploymentBundleHeader,
    DeploymentBundleSectionWriter,
    DeploymentBundleWriter,
    DeploymentDescriptor,
    DeploymentFiles,
    DeploymentIdentity,
    DeploymentProvenance,
    PlatformBundleSectionWriter,
    PlatformSensor,
    RawTelemetryBundleSectionWriter,
    VesselBundleSectionWriter,
    VesselSensor,
    open_deployment_bundle_writer,
)
from afft.seabed import Message, Topic

from .types import (
    BuildDeploymentBundleData,
    BuildDeploymentBundleDiagnostics,
    BuildDeploymentBundleResult,
)

SCHEMA_VERSION: str = "1.0.0"
BUILDER_VERSION: str = "1.0.0"


def build_files_frame(files: DeploymentFiles) -> pd.DataFrame:
    """
    Flatten a deployment's file manifest into one row per file.

    Arguments
    ---------
    files: Resolved file manifest for the deployment.

    Returns
    -------
    Frame with ``role`` and ``path`` columns, excluding ``root`` and ``other``.
    """
    rows: list[dict[str, str]] = []
    for role, value in files.model_dump(exclude={"root", "other"}).items():
        paths: list[Any] = (
            value if isinstance(value, list) else [value] if value else []
        )
        rows.extend({"role": role, "path": str(path)} for path in paths)
    return pd.DataFrame(rows)


def build_deployment_section(
    writer: DeploymentBundleSectionWriter,
    descriptor: DeploymentDescriptor,
    files: DeploymentFiles,
) -> None:
    """Write the bundle's ``deployment`` section."""
    writer.write_identity(
        DeploymentIdentity(
            deployment_label=descriptor.deployment_label,
            deployment_datetime=descriptor.deployment_datetime,
        )
    )
    writer.write_metadata(descriptor.metadata)
    writer.write_files(build_files_frame(files))
    writer.write_provenance(
        DeploymentProvenance(deployment_key=descriptor.deployment_label)
    )


def build_platform_section(
    writer: PlatformBundleSectionWriter, descriptor: DeploymentDescriptor
) -> None:
    """Write the bundle's ``platform`` section."""
    assert descriptor.platform.identity is not None
    writer.write_identity(descriptor.platform.identity)
    writer.write_sensors(descriptor.platform.sensors)


def build_vessel_section(
    writer: VesselBundleSectionWriter, descriptor: DeploymentDescriptor
) -> None:
    """Write the bundle's ``vessel`` section."""
    assert descriptor.vessel.identity is not None
    writer.write_identity(descriptor.vessel.identity)
    writer.write_sensors(descriptor.vessel.sensors)


def build_raw_telemetry_section(
    writer: RawTelemetryBundleSectionWriter,
    descriptor: DeploymentDescriptor,
    message_groups: dict[Topic, list[Message[Any, Any]]],
) -> None:
    """Write the bundle's ``telemetry/raw`` section, one table per topic."""
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
        frame: pd.DataFrame = pd.DataFrame(
            [message.to_dict() for message in messages]
        )
        frame = frame.rename(columns={"topic": "message_topic"})
        frame["sensor_key"] = topic_to_sensor_key[topic]
        writer.write(topic_to_sensor_key[topic], topic, frame)


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
        writer.write_header(
            DeploymentBundleHeader(
                schema_version=SCHEMA_VERSION,
                created_datetime=datetime.now(),
                builder_version=BUILDER_VERSION,
            )
        )
        build_deployment_section(writer.deployment, data.descriptor, data.files)
        build_platform_section(writer.platform, data.descriptor)
        build_vessel_section(writer.vessel, data.descriptor)
        build_raw_telemetry_section(
            writer.telemetry.raw, data.descriptor, data.message_groups
        )

    return BuildDeploymentBundleResult(
        deployment_label=data.descriptor.deployment_label,
        output_file=output_file,
        diagnostics=diagnostics,
    )
