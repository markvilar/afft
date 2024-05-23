"""Module for camera formatting task."""

from raft.services.renav import read_cameras
from raft.utils.log import logger

from .arguments import parse_arguments


def invoke_camera_formatting(arguments: list[str]) -> None:
    """Entrypoint for camera formatting task."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.err())

    namespace: Namespace = parse_result.ok()

    read_result: Result[PyDataFrame, str] = read_cameras(namespace.cameras)
    if read_result.is_err():
        logger.error(read_result.err())

    cameras: DataFrame = read_result.ok()

    if not namespace.selection:
        logger.error("no camera selection")

    raise NotImplementedError("invoke_camera_formatting is not implemented")
