""" Module for file transfer functionality. """
import logging

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Protocol

from loguru import logger
from icecream import ic

from .endpoint import Endpoint
from ..utils import get_time_string

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
class FileQueryData():
    """ Data class representation for a file query. """
    source: Endpoint
    destination: Endpoint
    includes: List[str] = field(default_factory=list)
    excludes: List[str] = field(default_factory=list)

def write_include_file(filepath: Path, includes: List[str]):
    with open(filepath, 'w') as f:
        for include in includes:
            f.write(f"{include}\n")

def get_path_end(path: Path, count: int) -> str:
    """ Get the last parts of a path. """
    return '/'.join(str(path).split('/')[-count:])

def query_files(
    context: TransferContext,
    data: FileQueryData,
):
    """ Execute a file search query. """

    # Write include keywords to file
    time = get_time_string()
    include_file_path = f"./.cache/{time}_includes.txt"
    write_include_file(include_file_path, data.includes) 
    
    result = context.copy(
        data.source, 
        data.destination, 
        flags=list(["--include-from", str(include_file_path)])
    )
    
    if result.flag != 0:
        logger.info(f"Transfer failed: {result.error}\n")

    return result
