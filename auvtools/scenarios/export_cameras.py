""" 
Scenarios for exporting of data including cameras, image groups, and sensor
messages. 
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from loguru import logger
from result import Ok, Err, Result

from ..camera.camera import Camera
from ..camera.writer import write_cameras_to_file
from ..filesystem import search_directory_tree, get_largest_file, make_directories
from ..services.renav import read_cameras_from_file

Cameras = List[Camera]
CameraSelector = Callable[[Cameras], Cameras]

@dataclass
class CameraExportData():
    """ Data class for camera export. 

    Attributes:
    - input_file: camera input file
    - output_file: camera output file
    - selector: strategy for selecting a subset of cameras
    """
    input_file: Path
    output_file: Path
    selector: Optional[CameraSelector] = None

def export_cameras(export_data: CameraExportData) -> Result[Path, str]:
    """ 
    Export cameras from a stereo pose data file. 
    
    Return:
        - result with output path or error message
    """
    # Read cameras from file
    read_result: Result[Cameras, str] = read_cameras_from_file(
        export_data.input_file
    )
    
    if read_result.is_err(): return read_result
    cameras = read_result.unwrap()

    # Match camera by indexed labels
    if export_data.selector:
        selected_cameras: Cameras = export_data.selector(cameras)
    else:
        selected_cameras = cameras

    # Make directories
    make_directories(str(export_data.output_file.parent), exist_ok=True)

    # Write cameras to file
    write_result = write_cameras_to_file(
        export_data.output_file,
        selected_cameras
    )

    if write_result.is_err(): return write_result
    return Ok(export_data.output_file)
