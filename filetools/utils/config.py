""" Module for reading and parsing configuration files. """

from configparser import ConfigParser
from pathlib import Path

def read_config_file(path: Path) -> ConfigParser:
    """ Read a config file. """
    assert path.is_file(), f"{path} is not a file"
    assert path.suffix in [".ini", ".toml"], "invalid config file extension"

    config = ConfigParser() 
    config.read(path)
    return config
