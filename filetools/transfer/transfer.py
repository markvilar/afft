""" Module for file transfer functionality. """
import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

import tqdm

from icecream import ic

import filetools.transfer.rclone_wrapper as rclone

@dataclass(unsafe_hash=True)
class FileTransfer():
    """ Data class to represent a transfer of multiple files. """
    source_dir: Path
    destination_dir: Path
    include_files: List[str] = field(default_factory=list)
    exclude_files: List[str] = field(default_factory=list)

@dataclass(unsafe_hash=True)
class DirectoryTransfer():
    """ Data class to represent a directory transfer. """
    source: Path
    destination: Path

@dataclass
class TransferAssignment():
    directory_transfers: List[DirectoryTransfer] = field(default_factory=list)
    file_transfers: List[FileTransfer] = field(default_factory=list)

@dataclass
class TransferJob():
    """ Data class for a transfer job. The job has an identifier label, and will
    attempt to resolved the queries with a given remote. """
    source: str
    label: str=str("")
    assignment: List[TransferAssignment] = field(default_factory=list)

def prepare_transfer(
    source: str,
    setup_fun: Callable[[], Dict[str, TransferAssignment]],
) -> List[TransferJob]:
    """ 
    Builder function to create a transfer job by setting up queries and 
    assigning a remote to the job. 

    Args:
     - source:        Source to transfer data from.
     - setup_fun:     Function to setup collections of transfer items.

    Return:
     - A list of transfer jobs.
    """
    assignments = setup_fun()
    transfer_jobs = list()
    for label, assignment in assignments.items():
        transfer_jobs.append(TransferJob(
            label=label,
            source=source,
            assignment=assignment,
    ))
    return transfer_jobs

def write_include_file(filepath: Path, includes: List[str]):
    with open(filepath, 'w') as f:
        for include in includes:
            f.write(f"{include}\n")

def execute_transfer(
    config: str,
    job: TransferJob,
    logger: logging.Logger=None,
):
    """ Executes a transfer job with a given context. """
    logger.info(f"Starting transfer: {job.label}")
    logger.info(f" -- Remote:      {job.source}")
    logger.info(f" -- File count:  {len(job.assignment.file_transfers)}")
    logger.info(f" -- Dir. count:  {len(job.assignment.directory_transfers)}\n")
    
    # Transfer directories
    iterator = tqdm.tqdm(
        job.assignment.directory_transfers, 
        desc="Transferring directories...",
    )
    
    for item in iterator: 
        source = f"{job.source}:{item.source}"
        destination = f"{item.destination}"

        # Execute rclone copy
        result = rclone.copy(config, source, destination, flags=list())

    # TODO: Set up include string

    # TODO: Transfer single files, look into --include flag
    for transfer in tqdm.tqdm(job.assignment.file_transfers, desc="Transferring files..."): 
        source = f"{job.source}:{transfer.source_dir}"
        destination = f"{transfer.destination_dir}"

        logger.info("\n")
        logger.info(f"Source:      {source}")
        logger.info(f"Destination: {destination}")

        # Write to filenames to txt file
        include_file_path = f"./cache/{job.label}_include_files.txt"
        write_include_file(include_file_path, transfer.include_files)
        
        result = rclone.copy(config, source, destination, 
            flags=[ "--include-from", str(include_file_path) ]
        )
