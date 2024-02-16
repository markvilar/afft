import json

from pathlib import Path
from typing import Any, Dict, Union

from result import Ok, Err, Result

JsonKey = Union[str, int, float]
JsonValue = Union[str, int, float, Dict]

JsonData = Dict[JsonKey, JsonValue]

def read_json(filepath: Path) -> Result[JsonData, str]:
    """ Reads a JSON file and returns the content as a dictionary. """
    if not filepath.exists():
        return Err(f"path does not exist: {filepath}")
    try:
        file_handle = open(filepath)
        data = json.load(file_handle)
        return Ok(data)
    except BaseException as error:
        return Err(str(error))
