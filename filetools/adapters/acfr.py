""" Module for ACFR specific logic and data formatting. """

import logging 

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from filetools.io import read_json
from filetools.transfer import TransferItem, TransferAssignment

@dataclass
class EntityData():
    label: str
    campaign: str
    deployment: str

@dataclass
class SequenceData():
    campaign: str
    deployment: str

def add_business_arguments(parser: ArgumentParser) -> ArgumentParser:
    """ Add business relevant arguments to an argument parser. """
    parser.add_argument("--config",
        type=Path,
        required=True,
        help="config file path",
    )
    return parser

def log_data_summary(data: Dict, logger: logging.Logger) -> None:
    """ Log a summary of data from ACFR. """
    logger.info("\n")
    logger.info(" ACFR Data ".center(80, '-'))
    logger.info(" - Group count: \n\t{0}".format(len(data.keys())))
    logger.info(" - Keys: \n\t{0}\n".format("\n\t".join(list(data.keys()))))

def prepare_directory(parent: Path, name: str, exist_ok: bool=False) -> Path:
    """ Prepares a directory by formatting the path and creating the 
    directory if it does not exist. """
    path = parent / name
    if not path.is_dir(): path.mkdir(exist_ok=exist_ok)
    return path

def filter_groups_by_label(data: Dict, labels: List[str]) -> Dict[str, List]:
    """ Filter groups whose label is not in the given labels. """
    groups = dict()
    for label in data:
        # Given filter labels, ignore if the label is not in them
        if labels and label not in labels:
            continue
        sequences = data[label]["groups"]
        groups[label] = sequences
    return groups

def get_entity_data(entity: Dict) -> EntityData:
    """ Extracts the data for an entity. """
    assert [key in entity for key in ["label", "survey"]], \
        "entity missing keys"
    label = entity["label"]["value"]
    campaign = entity["survey"]["campaign"]
    deployment = entity["survey"]["deployment"]
    return EntityData(label, campaign, deployment)

def get_sequence_data(sequence: Dict) -> SequenceData:
    """ Extracts the data for a sequence. """
    entities = sequence["entities"]
    entity_data = list()
    for key, entity in entities.items():
        entity_data.append(get_entity_data(entity))

    campaigns = set([entity.campaign for entity in entity_data])
    deployments = set([entity.deployment for entity in entity_data])

    assert len(campaigns) == 1, "multiple campaigns in sequence"
    assert len(deployments) == 1, "multiple deployments in sequence"

    return SequenceData(
        campaign=list(campaigns)[0],
        deployment=list(deployments)[0],
    )

def get_image_label_stem(label: str) -> str:
    """ Extracts the stem from an image stem. """
    splits = label.split("_")
    stem = "_".join(splits[:-1])
    return stem

def get_deployment_time(deployment: str) -> str:
    """ Extracts the datetime part of a deployment string. """
    assert len(deployment) >= 1, "invalid deployment string"
    splits = deployment[1:].split("_")
    assert len(splits) >= 2, "invalid deployment string"
    datetime = "_".join(splits[:2])
    return datetime

def create_sequence_transfers(
    source_dir: Path, 
    dest_dir: Path, 
    data: Dict
) -> Tuple[List[TransferItem], List[TransferItem]]:
    """ 
    Creates transfer items for a sequence of entities. 

    Args:
     - source_dir: source root directory
     - dest_dir:   destination root directory
     - data:       sequence data

    Returns:
     - Tuple of directory and file transfers
    """
    entities = data["entities"]
    dir_transfers = list()
    file_transfers = list()
    source_dirs, source_files = set(), set()
    for key in entities:
        entity = entities[key]

        # Get relevant data from entity and format source directory
        entity_data = get_entity_data(entity)
        campaign = entity_data.campaign
        deployment = entity_data.deployment
        datetime = get_deployment_time(deployment)

        # Format directory names
        data_dirs = {
            "img" : Path("i" + datetime),
            "bin" : Path("DT" + datetime),
            "msg" : Path("d" + datetime),
            "log" : Path("u" + datetime),
        }
       
        # Format source directories
        source_data_dirs = {
            "img" : source_dir / campaign / deployment / data_dirs["img"],
            "bin" : source_dir / campaign / deployment / data_dirs["bin"],
            "msg" : source_dir / campaign / deployment / data_dirs["msg"],
            "log" : source_dir / campaign / deployment / data_dirs["log"],
        }

        # Format destination directories (omitting campaign)
        dest_data_dirs = {
            "img" : dest_dir / data_dirs["img"],
            "bin" : dest_dir / data_dirs["bin"],
            "msg" : dest_dir / data_dirs["msg"],
            "log" : dest_dir / data_dirs["log"],
        }

        # NOTE: Create image directory
        dest_data_dirs["img"].mkdir(exist_ok=True)

        image_stem = get_image_label_stem(entity_data.label)
        image_files = {
            "left" : image_stem + "_LC16.tif", # NOTE: File extension
            "right" : image_stem + "_RM16.tif", # NOTE: File extension
        }

        # TODO: rclone copyto for single files
        # Create transfer item for left and right image
        """
        for key in ["left", "right"]:
            file_transfers.append(TransferItem(
                source=source_data_dirs["img"] / image_files[key],
                destination=dest_data_dirs["img"] / image_files[key],
            ))
        """

        # FIXME: Temporarily adding image directories
        dir_transfers.append(TransferItem(
                source=source_data_dirs["img"],
                destination=dest_data_dirs["img"],
        ))

        # Create transfer items for bin, msg and log directory
        for key in ["bin", "msg", "log"]:
            dir_transfers.append(TransferItem(
                source=source_data_dirs[key],
                destination=dest_data_dirs[key],
            ))

    # Remove duplicate directories
    dir_transfers = list(set(dir_transfers))
    return dir_transfers, file_transfers

def create_group_transfers(
    filepath: Path,
    target_labels: List[str],
    source_root: Path,
    dest_root: Path,
    logger: logging.Logger=None,
) -> Dict[str, TransferAssignment]:
    """ 
    Creates transfer items for groups of data from ACFR. 

    Args:
     - filepath:       Input file path with the grouped sequences
     - target_labels:  Labels used for targetted transferring
     - source_root:    Root directory at source
     - dest_root:      Root directory at destination

    Return:
     - Dictionary with group label and the corresponding transfer assignment.
    """
    # Load data from file
    data = read_json(filepath)

    # Log summary
    log_data_summary(data, logger)

    # Filter groups by label
    groups = filter_groups_by_label(data, target_labels)

    transfers = dict()
    for label, sequences in groups.items():
        # Create directory and set up transfer assignment for each group
        group_dir = prepare_directory(dest_root, label, exist_ok=True)
        assignment = TransferAssignment()
        for key, sequence in sequences.items():
            # Get sequence data and prepare directory
            sequence_data = get_sequence_data(sequence)
            sequence_dir = prepare_directory(
                group_dir, 
                sequence_data.deployment,
            )

            # Create transfer items
            dirs, files = create_sequence_transfers(
                source_root, 
                sequence_dir, 
                sequence,
            )
            
            # Extend the assignment with files and directories
            assignment.files.extend(files)
            assignment.directories.extend(dirs)

        # Add assignment to transfers
        transfers[label] = assignment
    return transfers
