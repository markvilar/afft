""" Module for reading and parsing configuration files. """

from configparser import ConfigParser
from pathlib import Path

def read_config_file(path: Path) -> ConfigParser:
    """ Read a config file. """
    assert path.suffix == ".ini", "invalid config file extension"
    config = ConfigParser() 
    config.read(path)
    return config
