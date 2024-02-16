""" Module for reading and parsing configuration files. """

from configparser import ConfigParser
from pathlib import Path
from typing import Dict

import toml

def read_toml(filepath: Path, mode: str="r") -> Dict:
    """ Read a toml file. """
    contents = None
    with open(filepath, mode) as filehandle:
        contents = toml.load(filehandle)
    return contents

def read_config_file(path: Path) -> ConfigParser:
    """ Read a config file. """
    assert path.is_file(), f"{path} is not a file"
    assert path.suffix in [".ini", ".toml"], "invalid config file extension"

    if path.suffix == ".toml":
        return read_toml(path)
    else:
        config = ConfigParser() 
        config.read(path)
        return config
