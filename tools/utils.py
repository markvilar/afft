""" Module with utility functionality, including argument parsing and logging. """

import logging
import sys

from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path

def read_config_file(path: Path) -> ConfigParser:
    """ Read a config file. """
    assert path.suffix == ".ini", "invalid config file extension"
    config = ConfigParser() 
    config.read(path)
    return config

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

def create_logger(name: str="client") -> logging.Logger:
    """ Creates a logger with a file and terminal sink. """
    logger = logging.Logger(name)
    logger.addHandler(logging.FileHandler(name + ".log"))
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger
