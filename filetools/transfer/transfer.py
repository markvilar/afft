""" Module for file transfer functionality. """
import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

import tqdm

from icecream import ic

import filetools.transfer.rclone as rclone

@dataclass(unsafe_hash=True)
class FileQuery():
    """ Data class to represent a transfer of multiple files. """
    source_dir: Path
    destination_dir: Path
    include_files: List[str] = field(default_factory=list)
    exclude_files: List[str] = field(default_factory=list)

@dataclass(unsafe_hash=True)
class DirectoryQuery():
    """ Data class to represent a directory transfer. """
    source: Path
    destination: Path

@dataclass
class TransferAssignment():
    directory_queries: List[DirectoryQuery] = field(default_factory=list)
    file_queries: List[FileQuery] = field(default_factory=list)

@dataclass
class TransferJob():
    """ Data class for a transfer job. The job has an identifier label, and will
    attempt to resolved the queries with a given remote. """
    source: str
    label: str=str("")
    assignment: TransferAssignment = None # TODO: Add multiple assignments?

def prepare_transfer(
    source: str,
    assignment_setup_fun: Callable[[], Dict[str, TransferAssignment]],
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
    assignments = assignment_setup_fun()
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
    config: str, # TODO: Change with Transfer context
    job: TransferJob,
    logger: logging.Logger=None,
):
    """ Executes a transfer job with a given context. """
    logger.info(f"Starting transfer: {job.label}")
    logger.info(f" -- Remote:           {job.source}")
    logger.info(f" -- File queries:     {len(job.assignment.file_queries)}")
    logger.info(f" -- Dir. queries:     {len(job.assignment.directory_queries)}\n")
    
    # Set up directory iterator
    iterator = tqdm.tqdm(
        job.assignment.directory_queries, 
        desc="Transferring directories...",
    )
    
    # Transfer directories
    for query in iterator: 
        source = f"{job.source}:{query.source}"
        destination = f"{query.destination}"
        
        logger.info("\n")
        logger.info(f"Source:      {source}")
        logger.info(f"Destination: {destination}")
       
        result = rclone.copy(config, source, destination, flags=list())
        
        logger.info(f"Rclone result: {result}")

    # Set up file iterator
    iterator = tqdm.tqdm(
        job.assignment.file_queries, 
        desc="Transferring files..."
    )

    # Transfer files
    for query in iterator: 
        source = f"{job.source}:{query.source_dir}"
        destination = f"{query.destination_dir}"

        # Write to filenames to txt file
        include_file_path = f"./.cache/{job.label}_includes.txt"
        write_include_file(include_file_path, query.include_files)
        
        result = rclone.copy(
            config, 
            source, 
            destination, 
            flags=list(["--include-from", str(include_file_path)])
        )

        logger.info(f"Rclone result: {result}")
