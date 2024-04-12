"""Main script - Entry point for export jobs."""

import argparse

from functools import partial
from pathlib import Path
from typing import Dict, List

from loguru import logger
from result import Ok, Err, Result

from auvtools.io import read_toml
from auvtools.messages.message_readers import read_message_lines_and_concatenate

from auvtools.jobs.format_messages import (
    MessageFormattingData,
    format_and_export_messages,
)


# NOTE: Refactor
from auvtools.scenarios.export_cameras import CameraExportData, export_cameras


ArgumentParser = argparse.ArgumentParser
Namespace = argparse.Namespace


def handle_message_formatting(input_dir: Path, output_dir: Path, config: Dict) -> None:
    """Handle message export job."""

    CONFIG_KEYS = ["name", "input_files", "output_file"]
    for key in CONFIG_KEYS:
        assert key in config, f"key not found in job config: {key}"

    # Prepend input and output directory paths to get absolute paths
    message_files = [input_dir / filepath for filepath in sorted(config["input_files"])]
    output_file = output_dir / config["output_file"]

    logger.info("Message files:")
    for path in message_files:
        logger.info(f" - {path.name}")

    formatting_data = MessageFormattingData(
        name=config["name"], message_files=message_files, output_file=output_file
    )

    for filepath in formatting_data.message_files:
        if not filepath.exists():
            logger.error(f"message file does not exists: {filepath}")

    # Read message files
    lines: List[str] = read_message_lines_and_concatenate(
        formatting_data.message_files
    ).unwrap()

    # TODO: Preprocess lines

    logger.info(f"Read and concatenated: {len(lines)} message lines")

    # TODO: Invoke message formatting job
    format_and_export_messages(
        reader=None,
        parser=None,
        exporter=None,
    )


def handle_camera_formatting(
    input_directory: Path, output_directory: Path, config: Dict
) -> None:
    """Handle camera export job."""
    raise NotImplementedError


def validate_arguments(arguments: Namespace) -> Result[Namespace, str]:
    """Validates arguments."""
    if not arguments.input.is_dir():
        return Err(f"invalid input directory: {arguments.input}")
    if not arguments.output.is_dir():
        return Err(f"invalid output directory: {arguments.output}")
    if not arguments.jobs.is_file():
        return Err(f"invalid job file: {arguments.jobs}")
    return Ok(arguments)


def main():
    """Entry point."""
    parser = ArgumentParser()
    parser.add_argument(
        "input",
        type=Path,
        help="input directory",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output directory",
    )
    parser.add_argument(
        "jobs",
        type=Path,
        help="path to job configuration file",
    )

    arguments: Namespace = validate_arguments(parser.parse_args()).unwrap()
    config = read_toml(arguments.jobs).unwrap()

    JOB_KEYS = ["message_formatting", "camera_formatting"]

    handlers = {
        "message_formatting": handle_message_formatting,
        # "camera_formatting": handle_camera_formatting,
    }

    for key in config:
        if key not in JOB_KEYS:
            logger.warning(f"invalid job key: {key}")
            continue

        if key not in handlers:
            logger.warning(f"missing job handler: {key}")
            continue

        jobs = config[key]
        for job in jobs:
            handlers[key](arguments.input, arguments.output, job)


if __name__ == "__main__":
    main()
