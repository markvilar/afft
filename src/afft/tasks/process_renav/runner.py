"""Runner for the process renav task."""

import pandas as pd

from afft.renav.readers import read_cameras
from afft.utils.log import logger

from .camera_processor import clean_camera_dataframe
from .types import ProcessRenavCommand


def run_process_renav(command: ProcessRenavCommand) -> None:
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

    cameras: pd.DataFrame = read_cameras(command.input_file)
    cameras = clean_camera_dataframe(cameras)
    cameras.to_csv(command.output_file, index=False)

    logger.info(
        f"{command.input_file.name}: {len(cameras)} pose(s) → "
        f"{command.output_file}"
    )
