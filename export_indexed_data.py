""" Process image and pose information. """
import argparse
import os

from functools import partial
from pathlib import Path
from typing import Dict, List

from loguru import logger
from result import Ok, Err, Result

from auvtools.camera.match import match_cameras_by_label
from auvtools.io import read_file, read_json
from auvtools.filesystem import (
    search_directory_tree, 
    get_largest_file,
    sort_paths_by_filename,
)

from auvtools.services.sirius import parse_messages
from auvtools.scenarios.export_cameras import CameraExportData, export_cameras
from auvtools.scenarios.export_messages import MessageExportData, export_messages

ArgumentParser = argparse.ArgumentParser
Namespace = argparse.Namespace

def validate_arguments(arguments: Namespace) -> Result[Namespace, str]:
    """ Validates arguments. """
    if not arguments.index.is_file():
        return Err(f"index is not a file: {arguments.index}")
    if not arguments.dataset.is_dir():
        return Err(f"dataset is not a directory: {arguments.dataset}")
    if not arguments.output.is_dir():
        return Err(f"output is not a directory: {arguments.output}")
    return Ok(arguments)

def prepare_message_export(
    input_directory: Path,
    output_directory: Path,
    metadata: Dict,
) -> MessageExportData:
    """ Prepares message export data for a visit. """
    # Find files with RAW AUV data
    search_result: Result[List[Path], str] = search_directory_tree(
        input_directory / "*.RAW.auv"
    )
    
    if search_result.is_err():
        logger.error(f"search error: {search_result.unwrap()}")

    # Sort files by name
    message_files: List[Path] = sort_paths_by_filename(search_result.unwrap())

    # Read message lines from all files and concatenate
    message_lines: List[str] = list()
    for path in message_files:
        result = read_file(path)
        if result.is_err():
            logger.error(f"read error: {result.unwrap()}")
        message_lines.extend(result.unwrap())

    # Parse messages
    messages: List[MessageData] = parse_messages(message_lines)

    datetime = metadata["datetime"]
    output_path = output_directory / f"{datetime}_messages.hdf5"
    return MessageExportData(messages, output_path)

def prepare_camera_export(
    input_directory: Path,
    output_directory: Path,
    metadata: Dict,
    components: Dict,
) -> CameraExportData:
    """ Prepares cameras export data for a visit. 

    Arguments:
    - input_directory: path to input directory
    - output_directory: path to output directory
    - metadata: dictionary of metadata fields (datetime, campaign, deployment)
    - components: dictionary of component fields (labels)

    Returns:
    - export_data: data for exporting cameras
    """
    # Search for camera files
    search_result: Result[List[Path], str] = search_directory_tree(
        input_directory / "*/stereo_pose_est.data"
    )

    if search_result.is_err():
        logger.error(f"search error: {search_result.unwrap()}")

    # Select strategy - Get camera file with the largest size
    camera_file = get_largest_file(search_result.unwrap())
    
    # Set up camera selection strategy
    selector = partial(
        match_cameras_by_label,
        targets = components["label"].values(),
    )

    # Set up export data
    export_data = CameraExportData(
        input_file = camera_file,
        output_file = output_directory / f"{metadata['datetime']}_cameras.csv",
        selector = selector,
    )

    if not export_data.input_file.exists():
        logger.error(f"path does not exist: {export_data.input_file}")

    return export_data

def prepare_site_export_scenarios(
    index_file: Path, 
    input_root: Path, 
    output_root: Path,
):
    """ Prepare paths for formatting scenarios.
    
    Arguments:
     - index_file: file containing visit directories, metadata, and components
     - input_root: root for input directory tree
     - output_root: root for output directory tree
    """
    read_result: Result[JsonData, str] = read_json(index_file)
    if read_result.is_err():
        logger.error(f"read error: {read_result.unwrap()}")
        return

    index = read_result.unwrap()
    
    site = index["site"]
    visits = index["visits"]
    data = index["data"]

    for visit in visits:
        # Extract visit data from the index file
        metadata = data[visit]["metadata"]
        directories = data[visit]["directories"]
        entities = data[visit]["entities"]
        components = data[visit]["components"]

        # Set up output directory for each visit
        output_directory = output_root / f"{site}/{metadata['deployment']}"

        # Prepare camera export data for each visit
        camera_export_data: CameraExportData = prepare_camera_export(
            input_root / directories["cameras"],
            output_directory,
            metadata, 
            components,
        )

        # Invoke camera export scenario
        export_result: Result[Path, str] = export_cameras(
            camera_export_data
        )

        match export_result:
            case Ok(path):
                logger.info(f"Wrote cameras to file: {path}")
            case Err(message):
                logger.error(export_result.unwrap())

        """
        # TODO: Prepare message export data
        message_export_data: MessageExportData = prepare_message_export(
            input_root / directories["messages"],
            output_directory,
            metadata, 
        )

        # TODO: Invoke message export data
        export_result: Result[Path, str] = export_messages(
            message_export_data
        )
        
        # TODO: Prepare image group export data
        """

def main():
    """ Entry point. """
    parser = ArgumentParser()
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
            prepare_site_export_scenarios(
                arguments.index, 
                arguments.dataset,
                arguments.output
            )
        case Err(message):
            logger.error(message)

if __name__ == "__main__":
    main()
