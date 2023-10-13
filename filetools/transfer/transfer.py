""" Module for file transfer functionality. """
import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

import tqdm

import filetools.transfer.rclone_wrapper as rclone

@dataclass(unsafe_hash=True)
class TransferItem():
    """ Data class for representing a transfer item. """
    source: Path
    destination: Path

@dataclass
class TransferAssignment():
    files: List[TransferItem] = field(default_factory=list)
    directories: List[TransferItem] = field(default_factory=list)

@dataclass
class TransferJob():
    """ Data class for a transfer job. The job has an identifier label, and will
    attempt to resolved the queries with a given remote. """
    source: str
    label: str=str("")
    assignment: TransferAssignment = field(default_factory=list)

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

def execute_transfer(
    config: str,
    job: TransferJob,
    logger: logging.Logger=None,
):
    """ Executes a transfer job with a given context. """
    logger.info(f"Starting transfer: {job.label}")
    logger.info(f" -- Remote:      {job.source}")
    logger.info(f" -- File count:  {len(job.assignment.files)}")
    logger.info(f" -- Dir. count:  {len(job.assignment.directories)}\n")

    # Transfer directories
    iterator = tqdm.tqdm(
        job.assignment.directories, 
        desc="Transferring directories...",
    )
    for item in iterator: 
        source = f"{job.source}:{item.source}"
        destination = f"{item.destination}"

        # Execute rclone copy
        result = rclone.copy(config, source, destination, flags=list())

    # TODO: Transfer single files, look into --include flag
    """
    for item in tqdm.tqdm(job.assignment.files, desc="Transferring images..."): 
        source = f"{job.source}:{item.source}"
        destination = f"{item.destination}"

        logger.info(f"\nSource:      {item.source}")
        logger.info(f"Destination: {item.destination}")
        
        result = rclone.copy_to(config, source, destination, flags=list())
    """
