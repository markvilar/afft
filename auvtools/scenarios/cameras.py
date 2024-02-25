""" Composed workflows for """
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from loguru import logger

from ..camera.camera import Camera
from ..camera.writer import write_cameras_to_file
from ..filesystem import search_directory_tree, get_largest_file, make_directories
from ..services.renav import read_cameras_from_file

Cameras = List[Camera]

@dataclass
class CameraExportData:
    """ Data class for camera export. """
    camera_directory: Path
    camera_file_pattern: str
    output_directory: Path
    output_filename: str

def export_camera_scenario(
    export_data: CameraExportData,
    select_strategy: Callable[[Cameras], Cameras]=None, 
) -> None:
    """ """
    # Search for camera files
    search_result: Result[List[Path], str] = search_directory_tree(
        export_data.camera_directory / "*/stereo_pose_est.data"
    )

    if search_result.is_err():
        logger.error(f"search error: {search_result.unwrap()}")
        return

    # Select strategy - Get camera file with the largest size
    camera_file = get_largest_file(search_result.unwrap())

    # Read cameras from file
    read_result: Result[Cameras, str] = read_cameras_from_file(camera_file)

    if read_result.is_err():
        logger.error(f"read error: {read_result.unwrap()}")

    cameras = read_result.unwrap()

    # Match camera by indexed labels
    matched_cameras: List[Camera] = select_strategy(cameras)

    # Make directories
    make_directories(str(export_data.output_directory), exist_ok=True)

    # Write cameras to file
    write_result = write_cameras_to_file(
        export_data.output_directory / export_data.output_filename, 
        matched_cameras
    )

    if write_result.is_err():
        logger.error(f"error when writing cameras: {write_result.unwrap()}")
        return

    logger.info(f"wrote cameras to file: {write_result.unwrap().name}\n")
