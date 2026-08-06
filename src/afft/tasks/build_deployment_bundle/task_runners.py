"""Runner for the build deployment bundle task."""

from typing import Any

import afft.seabed as seabed

from afft.deployment import (
    DeploymentDescriptor,
    DeploymentFiles,
    PlatformSensor,
    VesselSensor,
)
from afft.seabed import Topic
from afft.utils.log import logger

from .builders import build_deployment_bundle
from .task_helpers import (
    build_message_parser_registry,
    load_target_descriptor,
    read_raw_message_lines,
    validate_build_deployment_bundle_input,
)
from .types import (
    BuildDeploymentBundleCommand,
    BuildDeploymentBundleConfig,
    BuildDeploymentBundleData,
    BuildDeploymentBundleDiagnostics,
    BuildDeploymentBundleResult,
)


def run_build_deployment_bundle(
    command: BuildDeploymentBundleCommand,
    config: BuildDeploymentBundleConfig,
) -> BuildDeploymentBundleResult:
    """
    Build one deployment bundle from a descriptor and its raw message logs.

    Arguments
    ---------
    command: Task command.
    config: Task config, holding the topic-to-message-type mapping.

    Returns
    -------
    The build's result, including the run's diagnostics.
    """
    descriptor: DeploymentDescriptor = load_target_descriptor(
        command.descriptor_file, command.deployment_label
    )
    files: DeploymentFiles = validate_build_deployment_bundle_input(
        command, descriptor
    )

    logger.info("-------------------------------------")
    logger.info("Build Deployment Bundle")
    logger.info(f"  deployment label: {descriptor.deployment_label}")
    logger.info(f"  data dir:         {command.data_dir}")
    logger.info(f"  output file:      {command.output_file}")
    logger.info("-------------------------------------")

    registry: seabed.MessageParserRegistry = build_message_parser_registry(
        descriptor, config.message_map
    )
    lines: list[str] = read_raw_message_lines(files.raw_messages)
    parse_result: seabed.ParseMessageResult = seabed.parse_message_lines(
        lines, registry
    )

    message_groups: dict[Topic, list[seabed.Message[Any, Any]]] = {
        topic: sorted(messages, key=lambda message: message.header.timestamp)
        for topic, messages in parse_result.message_groups.items()
    }

    diagnostics = BuildDeploymentBundleDiagnostics()
    sensors: list[PlatformSensor | VesselSensor] = [
        *descriptor.platform.sensors,
        *descriptor.vessel.sensors,
    ]
    declared_topics: set[Topic] = {
        topic for sensor in sensors for topic in sensor.message_topics
    }
    for topic in declared_topics - message_groups.keys():
        diagnostics.warning(topic, "declared but no messages parsed")
    for topic, count in parse_result.failed.items():
        diagnostics.warning(topic, f"{count} line(s) failed to parse")

    data = BuildDeploymentBundleData(
        descriptor=descriptor,
        files=files,
        message_groups=message_groups,
    )

    result: BuildDeploymentBundleResult = build_deployment_bundle(
        command.output_file, data, diagnostics
    )
    logger.info(f"wrote deployment bundle to {result.output_file}")

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.topic}: {warning.message}")

    return result
