""" Module for ACFR specific logic and data formatting. """

from argparse import ArgumentParser
from logging import Logger
from pathlib import Path
from typing import Dict, List, Tuple

from icecream import ic

from filetools.io import read_json
from filetools.transfer import DirectoryTransfer, FileTransfer, TransferAssignment

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

def create_collection_transfer_assignment(
    source_directory: Path, 
    destination_directory: Path, 
    query_directories: List[str],
    query_files: List[str],
) -> TransferAssignment:
    """ 
    Creates transfer items for a sequence of entities. 

    Args:
     - source_directory:            source root directory
     - destination_directory:       destination root directory
     - directoires:                 target directories
     - files:                       target files
    Returns:
     - A transfer assignment with directories and files
    """
    ic(query_directories)
    input("Presss a key...")
    
    directory_transfers = list()
    for directory in query_directories:
        item = TransferItem(
            source = source_directory / directory,
            destination = destination_directory / directory,
        )
        directory_transfers.append(item)

    file_transfers = list()
    for file in query_files:
        item = TransferItem(
            # TODO: Add image directory
            source = source_directory / "**" / file,
            destination = destination_directory / "images" / file,
        )
        file_transfers.append(item)

    return TransferAssignment(
        files=file_transfers,
        directories=directory_transfers,
    )

def create_transfer_assignments(
    filepath: Path,
    source_root: Path,
    dest_root: Path,
    logger: Logger=None,
) -> Dict[str, List[TransferAssignment]]:
    """ 
    Creates transfer items for groups of data from ACFR. 

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

    # TODO: Filter groups by label
    # data = filter_groups_by_label(data, target_labels)
    selection = data

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

            # Set up query directories
            target_keys = ["bin", "log", "msg"]
            directory_transfers = list()
            for key in target_keys:
                directory_transfers.append(DirectoryTransfer(
                    source = source_directory / collection["directories"][key],
                    destination = destination_directory / collection["directories"][key],
                ))

            # TODO: Set up query files
            image_destination = prepare_directory(
                destination_directory, 
                "images",
                exist_ok=True,
            )

            file_transfers = list()
            file_transfers.append(
                FileTransfer(
                    source_dir = source_directory / collection["directories"]["img"],
                    destination_dir = image_destination,
                    include_files = collection["files"],
                )
            )

            assignment = TransferAssignment(
                directory_transfers = directory_transfers,
                file_transfers = file_transfers,
            )

            # Add assignment with the collection label to the transfer
            transfers[label] = assignment

    return transfers
