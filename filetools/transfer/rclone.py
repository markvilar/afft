""" Module for data transfer functionality. """
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from logging import Logger

import rclone

def local_config() -> str:
    """ Returns the configuration for a local remote. """
    return """[local] type=local nounc=true"""

def read_config(config_path: Path) -> str:
    """ Reads a configuration file as a string. """
    config = ""
    with open(config_path) as config_file:
        config += config_file.read()
    return config

def list_remotes(config: str) -> None:
    """ List the remotes for a given rclone configuration. """
    return rclone.with_config(config).listremotes()

def run_command(config: str, command: str, args: List[str]) -> None:
    """ Run a custom rclone command. """
    return rclone.with_config(config).run_cmd(
        command=command,
        extra_args=args,
    )

def copy_to(config: str, source: str, destination: str, flags: List[str]) -> Dict:
    """ 
    Copy files from the source to the destination.

    Args:
    - config:           rclone configuration string
    - source:           A string "source:path"
    - destination:      A string "dest:path"
    - flags:            Extra flags as per `rclone copy --help` 
    """
    return run_command(config, 
        command="copyto", 
        args=[source] + [destination] + flags,
    )

def copy(config: str, source: str, destination: str, flags: List[str]) -> Dict:
    """ 
    Copy a directory from the source to the destination.

    Args:
    - config:           rclone configuration string
    - source:           A string "source:/path/to/dir"
    - destination:      A string "dest:/path/to/dir"
    - flags:            Extra flags as per `rclone copy --help` 
    """
    return rclone.with_config(config).copy(
        source=source,
        dest=destination,
        flags=flags,
    )

def sync(local, remote) -> None:
    """ Sync a local and remote endpoint. """
    # NOTE: rclone.sync
    raise NotImplementedError

def list(reference, path: Path) -> None:
    """ Lists objects in a path with size and path. """
    # NOTE: rclone.ls
    raise NotImplementedError

def list_json(reference, path: Path) -> None:
    """ Lists objects in a path with size and path in JSON format. """
    # NOTE: rclone.lsjson
    raise NotImplementedError

def delete(reference, path: Path) -> None:
    """ Remove the objects of a path. """
    # NOTE: rclone.delete
    raise NotImplementedError
