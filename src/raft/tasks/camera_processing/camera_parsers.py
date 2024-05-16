""" Functionality to create pose references. """

import math
import re

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from loguru import logger
from result import Ok, Err, Result

from raft.camera import (
    Geolocation,
    Position3D,
    Orientation3D,
    ImageFile,
    Camera,
)

Cameras = List[Camera]

# -----------------------------------------------------------------------------
# ---- Pose file header -------------------------------------------------------
# -----------------------------------------------------------------------------


@dataclass
class RenavFileHeader:
    identifier: str
    version: str
    line_count: int
    text: str


def detect_header_line_count(lines: List[str]) -> int:
    """Returns the number of lines in the header."""
    count = 0
    for index, line in enumerate(lines):
        if len(line.split("\t")) > 10:
            count = index
            break
    return count


def parse_stereo_pose_header(lines: List[str]) -> Result[RenavFileHeader, str]:
    """Parse the header of a stereo pose file."""
    # Detect the
    line_count = detect_header_line_count(lines)
    header_lines = lines[:line_count]

    # Get header lines and string
    header_lines = [line.replace("% ", "") for line in header_lines]
    header_string = "\n".join(header_lines)

    # Set up regex searches
    search_results = dict()
    search_results["identifier"] = re.search(r"STEREO_POSE_FILE", header_string)
    search_results["version"] = re.search(r"VERSION\s*([\d.]+)", header_string)

    # Return errors if the following properties are not found
    if not search_results["identifier"]:
        return Err("unable to find stereo pose file identifier")
    if not search_results["version"]:
        return Err("unable to find stereo pose file version")

    # Get file identifier and version
    identifier = str(search_results["identifier"].group(0))
    version = str(search_results["version"].group(1))

    file_header = RenavFileHeader(
        identifier=identifier,
        version=version,
        line_count=line_count,
        text=header_string,
    )

    return Ok(file_header)


def rad_to_deg(radians: float) -> float:
    """Converts an angle from radians to degress."""
    return radians * 180.0 / math.pi


def format_stereo_pose(fields: List[str]) -> Camera:
    """Format a stereo pose from a pose file row."""
    fields = [field.strip() for field in fields]
    identifier = int(fields[0])
    timestamp = float(fields[1])
    label = Path(fields[10].strip()).stem

    geolocation = Geolocation(
        latitude=float(fields[2]),
        longitude=float(fields[3]),
        height=-float(fields[6]),
    )

    orientation = Orientation3D(
        roll=rad_to_deg(float(fields[7])),
        pitch=rad_to_deg(float(fields[8])),
        yaw=rad_to_deg(float(fields[9])),
    )

    left_filename = Path(fields[10].strip())
    right_filename = Path(fields[11].strip())

    # Check filenames for
    if len(str(left_filename)) != len(str(left_filename).strip()):
        logger.warning("left filename has tailed whitespaces")
    if len(str(right_filename)) != len(str(right_filename).strip()):
        logger.warning("right filename has tailed whitespaces")

    images = {
        "stereo_left": ImageFile(left_filename.stem, str(left_filename).strip()),
        "stereo_right": ImageFile(right_filename.stem, str(right_filename)),
    }

    accessories = {"altitude": float(fields[12]), "bounding_radius": float(fields[13])}

    return Camera(
        identifier=identifier,
        timestamp=timestamp,
        label=label,
        geolocation=geolocation,
        orientation=orientation,
        images=images,
        accessories=accessories,
    )


def parse_stereo_poses(
    lines: List[str],
    header: RenavFileHeader,
) -> Result[Cameras, str]:
    """Parse the rows of a stereo pose file."""
    # Get the lines that are not part of the header
    pose_lines = lines[header.line_count :]
    poses = list()
    for line in pose_lines:
        items = line.split("\t")
        pose: Camera = format_stereo_pose(items)
        poses.append(pose)
    return Ok(poses)


def read_cameras_from_file(path: Path) -> Result[Cameras, str]:
    """Reads camera poses from a Renav stereo pose file."""

    # TODO: Dispatch to stereo pose file reader
    if not path.is_file():
        return Err(f"{path} is not a file")

    with open(path, "r", encoding="utf-8") as filehandle:
        lines = filehandle.readlines()
        lines = [line.replace("\n", "") for line in lines]

        # Parse stereo pose header
        result = parse_stereo_pose_header(lines)

        if result.is_err():
            return Err("unable to read stereo pose header")

        # Parse stereo poses
        header = result.unwrap()
        result = parse_stereo_poses(lines, header)

        if result.is_err():
            return Err("unable to read stereo poses")

        poses = result.unwrap()

        return Ok(poses)
