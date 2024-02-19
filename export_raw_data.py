""" Process image and pose information. """
import os

from functools import partial
from pathlib import Path

from loguru import logger
from result import Ok, Err, Result

from auvtools.camera.match import match_cameras_by_label
from auvtools.io import read_json
from auvtools.utils import create_argument_parser, Namespace

from auvtools.scenarios.cameras import CameraExportData, export_camera_scenario

def validate_arguments(arguments: Namespace) -> Result[Namespace, str]:
    """ Validates arguments. """
    if not arguments.index.is_file():
        return Err(f"index is not a file: {arguments.index}")
    if not arguments.dataset.is_dir():
        return Err(f"dataset is not a directory: {arguments.dataset}")
    if not arguments.output.is_dir():
        return Err(f"output is not a directory: {arguments.output}")
    return Ok(arguments)

def prepare_format_input(
    index_file: Path, 
    dataset_directory: Path, 
    output_directory: Path,
):
    """ Prepare paths for formatting scenarios.
    
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
    
    # TODO: Set up export data
    site = index["site"]
    visits = index["visits"]
    data = index["data"]

    # For each visit - Format 
    for visit in visits:
        metadata = data[visit]["metadata"]
        directories = data[visit]["directories"]
        entities = data[visit]["entities"]
        components = data[visit]["components"]

        subdirectory = f"{site}/{metadata['deployment']}"

        # Set up export data
        export_data = CameraExportData(
            camera_directory = dataset_directory / directories["cameras"],
            camera_file_pattern = "*/stereo_pose_est.data",
            output_directory = output_directory / subdirectory,
            output_filename = f"{metadata['datetime']}_cameras.csv"
        )

        # Set up camera selection strategy
        selector = partial(
            match_cameras_by_label,
            targets = components["label"].values(),
        )

        
        if not export_data.camera_directory.exists():
            logger.error(f"path does not exist: {export_data.camera_directory}")
        
        status = export_camera_scenario(export_data, selector)

        # TODO: Set up image group maps
        # TODO: Parse messages


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
            prepare_format_input(
                arguments.index, 
                arguments.dataset,
                arguments.output
            )
        case Err(message):
            logger.error(message)

if __name__ == "__main__":
    main()
