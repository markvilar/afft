""" Module for reading and parsing command line arguments. """

from argparse import ArgumentParser
from pathlib import Path

def create_argument_parser() -> ArgumentParser:
    """ Creates an argument parser. """
    return ArgumentParser()

def add_remote_transfer_arguments(parser: ArgumentParser) -> ArgumentParser:
    """ Adds remote transfer arguments to an argument parser. """
    parser.add_argument("--rclone",
        type=Path,
        required=False,
        default=Path.home() / Path(".config/rclone/rclone.conf"),
        help="rclone config file path",
    )
    return parser
