"""Module for generating group descriptors."""

from raft.utils.log import logger

from .arguments import parse_arguments
from .data_types import MetafileGenerationContext
from .worker import generate_metafiles


def invoke_metafile_generation(arguments: list[str]) -> None:
    """Entrypoint for generating group metafiles."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.error())

    namespace: Namespace = parse_result.ok()

    context: MetafileGenerationContext = MetafileGenerationContext(
        root_directory=namespace.root,
        output_directory=namespace.output,
        prefix=namespace.prefix,
    )

    logger.info("")
    logger.info("Metafile generation:")
    logger.info(f" - Root:   {context.root_directory}")
    logger.info(f" - Output: {context.output_directory}")
    logger.info(f" - Prefix: {context.prefix}")
    logger.info("")

    generate_metafiles(context, namespace.config)
