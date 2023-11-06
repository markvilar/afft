import json

from pathlib import Path
from typing import Any, Dict, Union

JsonKey = Union[str, int, float]
JsonValue = Union[str, int, float, Dict]

def read_json(filepath: Path) -> Dict[JsonKey, JsonValue]:
    """ Reads a JSON file and returns the content as a dictionary. """
    file_handle = open(filepath)
    return json.load(file_handle)
