""" Functionality to write cameras to file. """

import csv

from pathlib import Path
from typing import List

from result import Ok, Err, Result

from .camera import Camera

Cameras = List[Camera]


def write_cameras_to_csv(path: Path, cameras: Cameras) -> Result[Path, str]:
    """Writes a collection of cameras to a CSV file."""
    with open(path, "w", newline="") as csvfile:
        fields = cameras[0].as_dict()

        writer = csv.DictWriter(csvfile, fieldnames=list(fields.keys()))
        writer.writeheader()

        for camera in cameras:
            fields = camera.as_dict()
            writer.writerow(fields)

    return Ok(path)


def write_cameras_to_file(path: Path, cameras: Cameras) -> Result[Path, str]:
    """Writes a collection of cameras to file."""
    if not path.parent.exists():
        return Err(f"parent directory does not exist: {path}")

    match path.suffix:
        case ".csv":
            return write_cameras_to_csv(path, cameras)
        case _:
            return Err(f"invalid file format: {path}")
    pass
