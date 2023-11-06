""" Module for file transfer functionality. """
import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Protocol

import tqdm

from icecream import ic

from .endpoint import Endpoint
#import filetools.transfer.rclone as rclone

@dataclass
class CommandResult():
    flag: int
    error: str
    output: List[str]

class TransferContext(Protocol):
    def copy(self, 
        source: Endpoint, 
        destination: Endpoint, 
        flags: List[str]
    ) -> CommandResult:
        """ Perform a transfer copy. """
        ...

@dataclass(unsafe_hash=True)
class FileQuery():
    """ Data class to represent a transfer of multiple files. """
    source: Path
    destination: Path
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
    label: str
    source: Endpoint
    destination: Endpoint
    assignment: TransferAssignment

QuerySetupFun = Callable[[], Dict[str, TransferAssignment]]

def prepare_transfer(
    source: Endpoint,
    destination: Endpoint,
    assignment_setup_fun: QuerySetupFun,
) -> List[TransferJob]:
    """ 
    Builder function to create a transfer job by setting up queries and 
    assigning a remote to the job. 

    Args:
     - source:        Source to transfer data from.
     - destination:   Source to transfer data from.
     - setup_fun:     Function to setup collections of transfer items.

    Return:
     - A list of transfer jobs.
    """
    assignments = assignment_setup_fun()
    transfer_jobs = list()
    for label, assignment in assignments.items():
        transfer_jobs.append(TransferJob(
            label = label,
            source = source,
            destination = destination,
            assignment = assignment,
        ))
    return transfer_jobs

def write_include_file(filepath: Path, includes: List[str]):
    with open(filepath, 'w') as f:
        for include in includes:
            f.write(f"{include}\n")

def get_path_end(path: Path, count: int) -> str:
    """ Get the last parts of a path. """
    return '/'.join(str(path).split('/')[-count:])

def execute_transfer(
    context: TransferContext,
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
        query_source = Endpoint(job.source.host, query.source)
        query_destination = Endpoint(job.destination.host, query.destination)
       
        logger.info("\n")
        logger.info(f"Source:       {get_path_end(query.source, 3)}")
        logger.info(f"Destination:  {get_path_end(query.destination, 3)}")
       
        result = context.copy(
            query_source, 
            query_destination, 
            flags=list(),
        )
        logger.info(f"Rclone result: {result}\n")

    # Set up file iterator
    iterator = tqdm.tqdm(
        job.assignment.file_queries, 
        desc="Transferring files..."
    )

    # Transfer files
    for query in iterator: 
        query_source = Endpoint(job.source.host, query.source)
        query_destination = Endpoint(job.destination.host, query.destination)

        # Write to filenames to txt file
        include_file_path = f"./.cache/{job.label}_includes.txt"
        write_include_file(include_file_path, query.include_files) 
        
        logger.info("\n")
        logger.info(f"Source:       {get_path_end(query.source, 3)}")
        logger.info(f"Destination:  {get_path_end(query.destination, 3)}")
        logger.info(f"Includes:     {include_file_path}")
        
        result = context.copy(
            query_source, 
            query_destination, 
            flags=list(["--include-from", str(include_file_path)])
        )
        logger.info(f"Rclone result: {result}\n")
