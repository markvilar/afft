""" Process image and pose information. """
import os

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from loguru import logger
from result import Ok, Err, Result

from auvtools.core.data import Camera, FileIndex
from auvtools.core.filesystem import (
    search_directory_tree, 
    get_path_size, 
    get_largest_file
)
from auvtools.core.io import read_json
from auvtools.core.utils import create_argument_parser, Namespace

from auvtools.services.renav import (
    read_cameras_from_file,
    write_cameras_to_file,
)

Cameras = List[Camera]

def validate_arguments(arguments: Namespace) -> Result[Namespace, str]:
    """ Validates arguments. """
    if not arguments.index.is_file():
        return Err(f"index is not a file: {arguments.index}")
    if not arguments.dataset.is_dir():
        return Err(f"dataset is not a directory: {arguments.dataset}")
    if not arguments.output.is_dir():
        return Err(f"output is not a directory: {arguments.output}")
    return Ok(arguments)

def match_cameras_by_label(
    cameras: Cameras, 
    targets: List[str],
) -> Dict[str, Camera]:
    """ Matches cameras with a list of targets based on their index. """
    matches = dict()
    for camera in cameras:
        if camera.label in targets:
            matches[camera.label] = camera
    return matches

def export_indexed_cameras(
    index_file: Path, 
    dataset_directory: Path, 
    output_directory: Path,
) -> None:
    """ Reads paths from a dataset index. 

    Arguments:
     - index_file: file containing directory paths, and labels
     - dataset_directory: target directory for input data
     - output_directory: target directory for output data
    """
    read_result: Result[JsonData, str] = read_json(index_file)
    if read_result.is_err():
        logger.error(f"read error: {read_result.unwrap()}")
        return

    index = read_result.unwrap()

    site = index["site"]
    visits = index["visits"]
    data = index["data"]
  
    # For each visit - Format 
    for visit in visits:
        metadata = data[visit]["metadata"]
        directories = data[visit]["directories"]
        entities = data[visit]["entities"]
        components = data[visit]["components"]

        # Set up camera directory path
        camera_directory = dataset_directory / directories["cameras"]
        if not camera_directory.exists():
            logger.error(f"path does not exist: {camera_path}")
        
        # Search for camera files
        search_result: Result[List[Path], str] = search_directory_tree(
            camera_directory / "*/stereo_pose_est.data"
        )

        if search_result.is_err():
            logger.error(f"search error: {search_result.unwrap()}")
            return
        
        # Get camera files and sizes
        camera_file = get_largest_file(search_result.unwrap())

        # Read cameras from file
        read_result: Result[Cameras, str] = read_cameras_from_file(camera_file)

        if read_result.is_err():
            logger.error(f"read error: {read_result.unwrap()}")
    
        cameras = read_result.unwrap()

        # Get labels from index
        target_labels = components["label"].values()

        # Match camera by indexed labels
        matched_cameras: Dict[str, Camera] = match_cameras_by_label(
            cameras, 
            target_labels,
        )

        match_count = len(matched_cameras)
        target_count = len(target_labels)
        
        logger.info(f"Camera matches: {match_count}/{target_count}")
        if match_count != target_count:
            logger.warning(f"unable to match {target_count-match_count} targets")
        
        # Use index to determine output directory
        subdirectory = f"{site}/{metadata['deployment']}"
        camera_filename = f"{metadata['datetime']}_cameras.csv"
        output_path = output_directory / subdirectory / camera_filename

        # Make directories
        os.makedirs(output_path.parent, exist_ok=True)
        
        write_result = write_cameras_to_file(
            output_path,
            list(matched_cameras.values()),
        )

        if write_result.is_err():
            logger.error(f"error when writing cameras: {write_result.unwrap()}")
            return

        logger.info(f"wrote cameras to file: {write_result.unwrap().name}\n")


def main():
    """ Entry point. """
    parser = create_argument_parser()
    parser.add_argument("index",
        type = Path,
        help = "dataset index file",
    )
    parser.add_argument("dataset",
        type = Path,
        help = "dataset directory",
    )
    parser.add_argument("output",
        type = Path,
        help = "output directory",
    )
    
    result: Result[Namespace, str] = validate_arguments(parser.parse_args())

    match result:
        case Ok(arguments):
            export_indexed_cameras(
                arguments.index, 
                arguments.dataset,
                arguments.output
            )
        case Err(message):
            logger.error(message)

if __name__ == "__main__":
    main()
