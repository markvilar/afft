"""Module for the entrypoint of the group export task."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from result import Ok, Err, Result

from raft.runtime.entrypoint import cli_entrypoint
from raft.utils.log import logger

from .data_types import FileExportContext
from .worker import execute_group_export


def parse_arguments(arguments: list[str]) -> Result[Namespace, str]:
    """Parses command-line arguments for metafile export tasks."""
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("data_directory", type=Path, help="data directory path")
    parser.add_argument("metafile", type=Path, help="metafile path")
    parser.add_argument("output_directory", type=Path, help="output directory path")
    parser.add_argument("--prefix", type=str, default="", help="output file prefix")

    namespace: Namespace = parser.parse_args(arguments)

    if not namespace:
        return Err("failed to parse arguments")
    else:
        return Ok(namespace)


def invoke_metafile_export(arguments: list[str]) -> None:
    """Entrypoint for metafile export tasks."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.err())

    namespace: Namespace = parse_result.ok()

    context: FileExportContext = FileExportContext(
        namespace.data_directory,
        namespace.metafile,
        namespace.output_directory,
        namespace.prefix,
    )

    execute_group_export(context)
