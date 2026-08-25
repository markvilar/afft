"""Supporting functions for the build deployment bundle task: descriptor
selection, config loading, input validation, and raw log parsing plumbing."""

from pathlib import Path
from typing import Any

import afft.io as io
import afft.seabed as seabed

from afft.deployment import (
    DeploymentDescriptor,
    DeploymentFiles,
    PlatformSensor,
    VesselSensor,
    collect_deployment_files,
    read_deployment_descriptors,
)

from .types import BuildDeploymentBundleCommand, BuildDeploymentBundleConfig


def load_target_descriptor(
    descriptor_file: Path,
    deployment_label: str,
) -> DeploymentDescriptor:
    """
    Select one deployment's descriptor out of a descriptors TOML file.

    Arguments
    ---------
    descriptor_file: Path to the deployment descriptors TOML file.
    deployment_label: Label of the deployment to select.

    Returns
    -------
    The matching descriptor.

    Raises
    ------
    ValueError: If no descriptor with the given label is present in the file.
    """
    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        descriptor_file
    )
    for descriptor in descriptors:
        if descriptor.deployment_label == deployment_label:
            return descriptor

    raise ValueError(f"deployment not found: {deployment_label!r}")


def read_build_deployment_bundle_config(
    config_file: Path,
) -> BuildDeploymentBundleConfig:
    """
    Read the builder's ``message_map`` section from the shared task config
    file.

    Arguments
    ---------
    config_file: Path to the shared task config TOML file.

    Returns
    -------
    The builder's config.
    """
    raw: dict[str, Any] = io.read_config(config_file)
    section: dict[str, Any] = raw["afft"]["tasks"]["build_deployment_bundle"]

    return BuildDeploymentBundleConfig(message_map=section["message_map"])


def build_message_parser_registry(
    descriptor: DeploymentDescriptor,
    topic_to_name: dict[seabed.Topic, seabed.MessageTypeName],
) -> seabed.MessageParserRegistry:
    """
    Build a message parser registry narrowed to the deployment's declared
    topics.

    Arguments
    ---------
    descriptor: Enriched descriptor for the deployment being built.
    topic_to_name: Mapping from message topic to message type name, from
        ``BuildDeploymentBundleConfig.message_map``.

    Returns
    -------
    A registry covering only the topics the deployment's platform and vessel
    sensors declare.
    """
    sensors: list[PlatformSensor | VesselSensor] = [
        *descriptor.platform.sensors,
        *descriptor.vessel.sensors,
    ]
    declared_topics: set[seabed.Topic] = {
        topic for sensor in sensors for topic in sensor.message_topics
    }

    topic_to_name = {
        topic: name
        for topic, name in topic_to_name.items()
        if topic in declared_topics
    }

    return seabed.build_message_parser_registry(topic_to_name)


def validate_build_deployment_bundle_input(
    command: BuildDeploymentBundleCommand,
    descriptor: DeploymentDescriptor,
) -> DeploymentFiles:
    """
    Validate the task's inputs before any expensive work runs.

    Arguments
    ---------
    command: Task command.
    descriptor: Descriptor resolved from ``command.descriptor_file`` and
        ``command.deployment_label``.

    Returns
    -------
    The deployment's re-globbed file manifest, for reuse by the caller.

    Raises
    ------
    FileNotFoundError: If ``data_dir`` or the output directory does not
        exist, or if no raw message logs are found.
    ValueError: If ``data_dir``'s name does not match the deployment label,
        the descriptor is unenriched, or the output file already exists and
        ``command.overwrite`` is not set.
    """
    if not command.data_dir.is_dir():
        raise FileNotFoundError(
            f"data directory does not exist: {command.data_dir}"
        )
    expected_dir_name: str = f"{descriptor.deployment_label}_deployment_data"
    if command.data_dir.name != expected_dir_name:
        raise ValueError(
            f"data directory {command.data_dir.name!r} does not match "
            f"deployment label {descriptor.deployment_label!r} "
            f"(expected {expected_dir_name!r})"
        )

    if (
        descriptor.platform.identity is None
        or descriptor.vessel.identity is None
    ):
        raise ValueError(
            f"descriptor for {descriptor.deployment_label!r} is not enriched"
        )

    files: DeploymentFiles = collect_deployment_files(command.data_dir)
    if not files.raw_messages:
        raise FileNotFoundError(
            f"no raw message logs found under {command.data_dir}"
        )

    if not command.output_file.parent.is_dir():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )
    if command.output_file.exists():
        if not command.overwrite:
            raise ValueError(
                f"output file already exists: {command.output_file}"
            )
        command.output_file.unlink()

    return files


def read_raw_message_lines(raw_messages: list[Path]) -> list[str]:
    """
    Concatenate lines from every raw message log file, in a deterministic
    order.

    Arguments
    ---------
    raw_messages: Raw message log files, from the deployment's file manifest.

    Returns
    -------
    All lines from every file, files sorted by filename.
    """
    lines: list[str] = []
    for raw_file in sorted(raw_messages):
        lines.extend(io.read_lines(raw_file))
    return lines
