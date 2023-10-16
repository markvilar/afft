""" Module for ACFR specific logic and data formatting. """

from logging import Logger
from pathlib import Path
from typing import Dict, List

from icecream import ic

from filetools.io import read_json
from filetools.transfer import DirectoryQuery, FileQuery, TransferAssignment

from .format import replace_file_extensions, append_wildcard_to_prefix

def prepare_directory(parent: Path, name: str, exist_ok: bool=False) -> Path:
    """ Prepares a directory by formatting the path and creating the 
    directory if it does not exist. """
    path = parent / name
    if not path.is_dir(): path.mkdir(exist_ok=exist_ok)
    return path

    # Log summary
def log_data_summary(data: Dict, logger: Logger) -> None:
    """ Log a summary of the data from the query file. """
    logger.info(f"\nData: {len(data.keys())} groups")
    for group in data:
        collections = data[group]
        logger.info(f" - Group {group}: {len(collections)} collections")
    logger.info("\n")

def filter_groups_by_label(data, target_groups) -> List[str]:
    """ Adds keys from data that are in the target groups. """
    selection = list()
    for target in target_groups:
        if target in data:
            selection.append(target)
    return selection

def create_group_queries(
    filepath: Path,
    source_root: Path,
    dest_root: Path,
    target_groups: List[str]=None,
    logger: Logger=None,
) -> Dict[str, List[TransferAssignment]]:
    """ 
    Creates queries for groups of data from ACFR. 

    Args:
     - filepath:       Input file path with the grouped sequences
     - target_labels:  Labels used for targetted transferring
     - source_root:    Root directory at source
     - dest_root:      Root directory at destination

    Return:
     - Dictionary with job label and corresponding assignments
    """
    # Load data from file
    data = read_json(filepath)

    # Log summary
    log_data_summary(data, logger)

    if target_groups:
        selection = filter_groups_by_label(data, target_groups)
    else:
        selection = list(data.keys())

    ic(type(target_groups), target_groups)
    ic(type(selection), selection)
    input("Press a key...")

    transfers = dict()
    for group in selection:
        # Create directory and set up transfer assignment for each group
        group_directory = prepare_directory(dest_root, group, exist_ok=True)

        collections = data[group]
        
        assignment = TransferAssignment()
        for label in collections:

            collection = collections[label]
            
            source_directory = source_root / collection["root"]

            # Only use deployment as root for the 
            root = collection["root"].split("/")[-1]

            # Prepare the collection directory
            destination_directory = prepare_directory(
                group_directory, 
                root,
                exist_ok=True,
            )

            # Set up directory queries
            target_keys = ["bin", "log", "msg"]
            directory_queries = list()
            for key in target_keys:
                directory_transfer = DirectoryQuery(
                    source = source_directory / collection["directories"][key],
                    destination = destination_directory / collection["directories"][key],
                )
                directory_queries.append( directory_transfer )

            image_destination = prepare_directory(
                destination_directory, 
                "images",
                exist_ok=True,
            )

            # Set up file queries
            file_queries = list()
            file_query = FileQuery(
                source_dir = source_directory / collection["directories"]["img"],
                destination_dir = image_destination,
                include_files = collection["files"],
            )
            file_queries.append(file_query)

            # Format the include items by appending wildcards to the
            # second-level label
            for transfer in file_transfers:
                updated_includes = append_wildcard_to_prefix(
                    filepaths = transfer.include_files,
                    prefix_length = 19,
                    wildcard = "*",
                )
                transfer.include_files = updated_includes
            
            assignment = TransferAssignment(
                directory_queries = directory_queries,
                file_queries = file_queries,
            )

            # Add assignment with the collection label to the transfer
            transfers[label] = assignment

    return transfers
