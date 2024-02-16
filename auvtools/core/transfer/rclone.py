""" Module for data transfer functionality. """
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union
from logging import Logger

import rclone

from .endpoint import Endpoint
from .transfer import CommandResult

CommandLineOutput= Dict[str, Union[str, int, float, bytes]]

def parse_command_line_result(result: CommandLineOutput) -> CommandResult:
    """ Parse the result from command as a result data class. """
    flag = result["code"]
    error = result["error"].decode("utf-8")
    output = [ 
        string.strip()
        for string in result["out"].decode("utf-8").split(" -1 ")
        if not string.isspace()
    ]
    return CommandResult(flag, error, output)

def local_config() -> str:
    """ Returns the configuration for a local remote. """
    return """[local]\ntype = local\nnounc = true"""

def read_config(config_path: Path) -> str:
    """ Reads a configuration file as a string. """
    config = ""
    with open(config_path) as config_file:
        config += config_file.read()
    return config

class Context():
    def __init__(self, config) -> object:
        """ Constructor method. """
        self.config = config
        self.config += local_config()

    def copy(self, 
        source: Endpoint, 
        destination: Endpoint, 
        flags: List[str],
    ) -> CommandResult:
        """ Perform a copy with a rclone context. """
        result = rclone.with_config(self.config).copy(
            source = source.as_string(),
            dest = destination.as_string(),
            flags = flags,
        )
        return parse_command_line_result(result)

"""
Rclone actions:
 - run_command
 - list_remotes
 - list_directories
"""

def run_command(
    context: Context,
    command: str, 
    args: List[str]
) -> CommandLineOutput:
    """ Run a custom rclone command. """
    return rclone.with_config(context.config).run_cmd(
        command=command,
        extra_args=args,
    )

def list_remotes(context: Context) -> None:
    """ List the remotes for a given rclone configuration. """
    return rclone.with_config(context.config).listremotes()

def list_directories(
    context: Context, 
    host: str, 
    path: Path, 
    flags: List[str]=list()
) -> CommandResult:
    """ List all directories in the source path. """
    endpoint = f"{host}:{path}"
    result = run_command(
        context, 
        command="lsd", 
        args=[endpoint] + flags,
    )
    return parse_command_line_result(result)

def copy(context: Context, source: str, destination: str, flags: List[str]) -> Dict:
    """ 
    Copy a directory from the source to the destination.

    Args:
    - config:           rclone configuration string
    - source:           A string "source:/path/to/dir"
    - destination:      A string "dest:/path/to/dir"
    - flags:            Extra flags as per `rclone copy --help` 
    """
    result = rclone.with_config(context.config).copy(
        source = source,
        dest = destination,
        flags = flags,
    )
    return parse_command_line_result(result)

def sync(local, remote) -> None:
    """ Sync a local and remote endpoint. """
    # NOTE: rclone.sync
    raise NotImplementedError

# TODO: Rename
#def list(reference, path: Path) -> None:
#    """ Lists objects in a path with size and path. """
#    # NOTE: rclone.ls
#    raise NotImplementedError


def list_json(reference, path: Path) -> None:
    """ Lists objects in a path with size and path in JSON format. """
    # NOTE: rclone.lsjson
    raise NotImplementedError

def delete(reference, path: Path) -> None:
    """ Remove the objects of a path. """
    # NOTE: rclone.delete
    raise NotImplementedError
