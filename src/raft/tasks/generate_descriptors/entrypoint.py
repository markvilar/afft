"""Module for generating group descriptors."""

from raft.utils.log import logger

from .arguments import parse_arguments
from .executor import generate_group_descriptors


def invoke_group_descriptor_generation(arguments: list[str]) -> None:
    """Entrypoint for generating group descriptors."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.error())

    namespace: Namespace = parse_result.ok()

    logger.info("")
    logger.info("Descriptor generation:")
    logger.info(f" - Root:   {namespace.root}")
    logger.info(f" - Output: {namespace.output}")
    logger.info(f" - Prefix: {namespace.prefix}")
    logger.info("")

    generate_group_descriptors(namespace.root, namespace.output, namespace.prefix)
