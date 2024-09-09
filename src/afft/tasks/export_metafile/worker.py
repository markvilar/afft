"""Module for executing file export tasks from metafiles."""

from pathlib import Path
from typing import Callable

from ...filesystem import get_path_size, copy_file
from ...io import read_file, read_toml, write_file
from ...utils.log import logger
from ...utils.result import Result

from .data_types import FileExportContext


def select_largest_file(files: list[Path]) -> Path:
    """Returns the file with the largest size."""

    size_results: dict[Path : Result[int, str]] = {
        path: get_path_size(path) for path in files
    }

    file_sizes: dict[Path, int] = dict()
    for path, result in size_results.items():
        if result.is_err():
            logger.error(f"failed to get size for path: {path}")
            continue

        file_sizes[path]: int = result.ok()

    selected: Path = max(file_sizes, key=file_sizes.get)
    return selected


FileSelector = Callable[[list[Path]], Path]


def export_camera_files(
    context: FileExportContext,
    group: str,
    camera_files: list[Path],
    file_selector: FileSelector,
) -> None:
    """Selects a camera file and copies it to the output directory."""

    selected: Path = file_selector(camera_files)

    output_directory: Path = context.output_directory
    output_filepath: Path = output_directory / f"{context.prefix}_{group}_cameras.csv"

    copy_result: Result[Path, str] = copy_file(
        source=selected, destination=output_filepath
    )

    if copy_result.is_err():
        logger.error(copy_result.err())
    else:
        logger.info(f"Copied file: {selected.name} -> {copy_result.ok()}")


def export_message_files(
    context: FileExportContext, group: str, message_files: list[Path]
) -> None:
    """Reads and merges the data from a collection of message files, and writes the data to a single message file."""

    # Validate message files
    for message_file in message_files:
        if not message_file.exists():
            logger.error(f"path does not exist: {message_file}")
        if not message_file.is_file():
            logger.error(f"path is not a file: {message_file}")

    # Load and concatenate data
    read_results: list[Result[list[str], str]] = [
        read_file(path) for path in message_files
    ]

    message_lines: list[str] = list()
    for result in read_results:
        if result.is_err():
            logger.error(result.err())

        lines: list[str] = result.ok()
        message_lines.extend(lines)

    output_directory: Path = context.output_directory
    output_filepath: Path = output_directory / f"{context.prefix}_{group}_messages.txt"

    write_result: Result[Path, str] = write_file(message_lines, output_filepath)

    if write_result.is_err():
        logger.error(write_result)

    logger.info(f"wrote messages to file: {write_result.ok()}")


def execute_group_export(context: FileExportContext) -> None:
    """Executes export tasks for a file group."""

    logger.info("")
    logger.info("File group export:")
    logger.info(f" - Data directory:        {context.data_directory}")
    logger.info(f" - Metafile:              {context.metafile}")
    logger.info(f" - Output directory:      {context.output_directory}")
    logger.info(f" - Prefix:                {context.prefix}")
    logger.info("")

    read_result: Result[dict, str] = read_toml(context.metafile)
    if read_result.is_err():
        logger.error(read_result.err())
        return

    file_groups: dict = read_result.ok()

    for entry in file_groups["visit"]:

        message_files: list[Path] = [
            context.data_directory / Path(item) for item in entry["messages"]
        ]
        camera_files: list[Path] = [
            context.data_directory / Path(item) for item in entry["cameras"]
        ]

        export_message_files(context, entry["name"], message_files)

        export_camera_files(
            context, entry["name"], camera_files, file_selector=select_largest_file
        )
