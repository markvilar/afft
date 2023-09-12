import json

from pathlib import Path
from typing import Dict

def read_json(filepath: Path) -> Dict:
    """ Reads a JSON file and returns the content as a dictionary. """
    file_handle = open(filepath)
    return json.load(file_handle)
