"""Module for camera filtering task."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from ...utils.log import logger
from ...utils.result import Ok, Err, Result

from .data_types import CameraFilteringContext
from .worker import filter_cameras


def parse_arguments(arguments: list[str]) -> Result[Namespace, str]:
    """Creates an argument parser."""
    parser = ArgumentParser()
    parser.add_argument("cameras", type=Path, help="camera file path")
    parser.add_argument("output", type=Path, help="output file path")
    parser.add_argument("--labels", type=Path, help="labels file path")

    namespace: Namespace = parser.parse_args(arguments)

    if not namespace:
        return Err("invalid arguments")
    else:
        return Ok(namespace)


def invoke_camera_filtering(arguments: list[str]) -> None:
    """Entrypoint for camera filtering task."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.err())

    namespace: Namespace = parse_result.ok()

    context: CameraFilteringContext = CameraFilteringContext(
        camera_file=namespace.cameras,
        output_file=namespace.output,
        label_file=namespace.labels if namespace.labels else None,
    )

    logger.info("")
    logger.info("Camera filtering:")
    logger.info(f" - Input file:  {context.camera_file}")
    logger.info(f" - Output file: {context.output_file}")
    if context.has_labels:
        logger.info(f" - Label file:  {context.label_file}")
    logger.info("")

    filter_cameras(context)
