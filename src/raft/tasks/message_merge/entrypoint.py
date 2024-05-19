"""Module for formatting AUV messages including reading, preprocessing,
parsing, and exporting."""

import argparse

from pathlib import Path
from typing import Dict, List

from raft.io import write_file
from raft.services.sirius_messages import process_message_lines, read_message_lines
from raft.utils.log import logger

from .config import MessageMergeBatch, MessageMergeConfig, configure_task
from .arguments import parse_arguments


def execute_message_merging(config: MessageMergeConfig) -> None:
    """Execute for message formatting."""

    logger.info("Executing message merge subtask:")
    logger.info(f" - Name:   {config.name}")
    logger.info(f" - Input:  {config.directories.input}")
    logger.info(f" - Output: {config.directories.output}")
    logger.info("")
    logger.info(" - Message files:  ")
    for file in config.message_files:
        logger.info(f"   - {file}")

    lines: list[str] = list()
    for file in sorted(config.message_files):
        filepath: Path = config.directories.input / file
        
        read_result: Result[list[str], str] = read_message_lines(filepath)
        if read_result.is_err():
            logger.error(read_result.err())
            return

        new_lines: list[str] = read_result.ok()
        
        logger.debug(f"read {len(new_lines)} messages from {filepath}")
        lines.extend(new_lines)
        
    # Replace tabs with whitespaces to simplify processing down the line.
    lines: list[str] = [line.replace("\t", "    ") for line in lines]

    output_path: Path = config.directories.output / f"{config.name}_messages.txt"

    write_result: Result[Path, str] = write_file(lines, output_path)
    if write_result.is_err():
        logger.error(write_result.err())
        return


def invoke_message_merging(arguments: List[str]) -> None:
    """Entrypoint for merging message files."""

    parse_result: Result[Namespace, str] = parse_arguments(arguments)
    if parse_result.is_err():
        logger.error(parse_result.err())

    namespace: Namespace = parse_result.ok()

    batch: MessageMergeBatch = configure_task(namespace.input, namespace.output, namespace.subtasks)

    for subtask in batch.subtasks:
        execute_message_merging(subtask)
