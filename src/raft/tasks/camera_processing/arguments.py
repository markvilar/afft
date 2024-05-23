"""Module for camera processing arguments."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from result import Ok, Err, Result


def parse_arguments(arguments: list[str]) -> Result[Namespace, str]:
    """Creates an argument parser."""
    parser = ArgumentParser()
    parser.add_argument("cameras", type=Path, help="camera file path")
    parser.add_argument("output", type=Path, help="output directory")
    parser.add_argument("--selection", type=Path, help="selection file path")

    # TODO: Add config file argument
    # parser.add_argument("config", type=Path, help="configuration file path")

    namespace: Namespace = parser.parse_args(arguments)

    if not namespace:
        return Err("invalid arguments")
    else:
        return Ok(namespace)
