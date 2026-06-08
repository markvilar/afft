"""Runner for the process renav task."""

from pathlib import Path

import pandas as pd

from afft.renav.readers import read_cameras
from afft.utils.log import logger

from .camera_processor import clean_camera_dataframe
from .types import ProcessRenavPosesBatchCommand, ProcessRenavPosesCommand


def _process_file(input_file: Path, output_file: Path) -> int:
    cameras: pd.DataFrame = read_cameras(input_file)
    cameras = clean_camera_dataframe(cameras)
    cameras.to_csv(output_file, index=False)
    return len(cameras)


def run_process_renav_poses(command: ProcessRenavPosesCommand) -> None:
    """
    Read, clean, and write a Renav stereo pose estimate file to CSV.

    Arguments
    ---------
    command: Task configuration.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    row_count: int = _process_file(command.input_file, command.output_file)
    logger.info(
        f"{command.input_file.name}: {row_count} pose(s) → {command.output_file}"
    )


def run_process_renav_poses_batch(
    command: ProcessRenavPosesBatchCommand,
) -> None:
    """
    Read, clean, and write all matching Renav stereo pose estimate files in a
    directory to CSV.

    Arguments
    ---------
    command: Task configuration.
    """
    if not command.input_dir.exists():
        raise FileNotFoundError(
            f"input directory does not exist: {command.input_dir}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )

    input_files: list[Path] = sorted(command.input_dir.glob(command.pattern))
    if not input_files:
        raise FileNotFoundError(
            f"no files matching '{command.pattern}' in {command.input_dir}"
        )

    logger.info(
        f"processing {len(input_files)} file(s) from {command.input_dir}"
    )

    for input_file in input_files:
        output_file: Path = (
            command.output_dir / input_file.with_suffix(".csv").name
        )
        row_count: int = _process_file(input_file, output_file)
        logger.info(
            f"  {input_file.name}: {row_count} pose(s) → {output_file.name}"
        )
