"""Package for various IO functionality, such as reading data from and writing data to files."""

from .config_io import read_config as read_config
from .config_io import write_config as write_config

from .file_io import read_lines as read_lines
from .file_io import write_lines as write_lines


__all__ = []
