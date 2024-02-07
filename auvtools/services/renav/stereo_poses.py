""" Functionality to create pose references. """
import csv
import math
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from result import Ok, Err, Result

IDENTIFIERS = {
    "filetype" : "STEREO_POSE_FILE",
    "version" : "VERSION",
}

FieldDescriptor = Tuple[str, type]

POSE_FIELD_DESCRIPTORS: Dict[str, FieldDescriptor] = {
    0  : ( "identifier",      int   ),
    1  : ( "timestamp",       float ),
    2  : ( "latitude",        float ),
    3  : ( "longitude",       float ),
    4  : ( "position_x",      float ),
    5  : ( "position_y",      float ),
    6  : ( "position_z",      float ),
    7  : ( "orientation_x",   float ),
    8  : ( "orientation_y",   float ),
    9  : ( "orientation_z",   float ),
    10 : ( "image_left",      str   ),
    11 : ( "image_right",     str   ),
    12 : ( "altitude",        float ),
    13 : ( "bounding_radius", float ),
    14 : ( "cross_over",      bool  ),
}

@dataclass
class PoseFileHeader():
    identifier: str
    version: str
    line_count: int
    text: str

@dataclass
class Geolocation():
    latitude: float
    longitude: float
    height: float

@dataclass
class Position3D():
    x: float
    y: float
    z: float

@dataclass
class Orientation3D():
    roll: float
    pitch: float
    yaw: float

@dataclass
class ImageFile():
    label: str
    filename: str

@dataclass
class StereoPose():
    identifier: str
    label: str
    timestamp: float
    geolocation: Geolocation
    position: Position3D
    orientation: Orientation3D
    master: ImageFile
    slave: ImageFile
    altitude: Optional[float]
    footprint: Optional[float]

StereoPoses = List[StereoPose]

# -----------------------------------------------------------------------------
# ---- Stereo pose header -------------------------------------------------------
# -----------------------------------------------------------------------------

def detect_header_line_count(lines: List[str]) -> int:
    """ Returns the number of lines in the header. """
    count = 0
    for index, line in enumerate(lines):
        if len(line.split("\t")) > 10:
            count = index
            break
    return count

def parse_stereo_pose_header(lines: List[str]) -> Result[PoseFileHeader, str]:
    """ Parse the header of a stereo pose file. """
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

    file_header = PoseFileHeader(
        identifier = identifier,
        version = version,
        line_count = line_count,
        text = header_string,
    )
    
    return Ok(file_header)

# -----------------------------------------------------------------------------
# ---- Stereo pose rows -------------------------------------------------------
# -----------------------------------------------------------------------------

def rad_to_deg(radians: float) -> float:
    """ Converts an angle from radians to degress. """
    return radians * 180.0 / math.pi

def format_stereo_pose(fields: List[str]) -> StereoPose:
    """ Format a stereo pose from a pose file row. """
    identifier = int(fields[0])
    timestamp = float(fields[1])
    label = Path(fields[10]).stem
    geolocation = Geolocation(
        latitude = float(fields[2]),
        longitude = float(fields[3]),
        height = -float(fields[6]),
    )
    position = Position3D(
        x = float(fields[4]),
        y = float(fields[5]),
        z = float(fields[6]),
    )
    orientation = Orientation3D(
        roll = rad_to_deg(float(fields[7])),
        pitch = rad_to_deg(float(fields[8])),
        yaw = rad_to_deg(float(fields[9])),
    )
    master_image = ImageFile(
        label = Path(fields[10]).stem,
        filename = str(fields[10]),
    )
    slave_image = ImageFile(
        label = Path(fields[11]).stem,
        filename = str(fields[11]),
    )
    altitude = float(fields[12])
    footprint = float(fields[13]) * 2.0

    return StereoPose(
        identifier = identifier,
        timestamp = timestamp,
        label = label,
        geolocation = geolocation,
        position = position,
        orientation = orientation,
        master = master_image,
        slave = slave_image,
        altitude = altitude,
        footprint = footprint,
    )

def parse_stereo_poses(
    lines: List[str], 
    header: PoseFileHeader,
) -> Result[StereoPoses, str]:
    """ Parse the rows of a stereo pose file. """
    # Get the lines that are not part of the header
    pose_lines = lines[header.line_count:]
    poses = list()
    for line in pose_lines:
        items = line.split("\t")
        pose: StereoPose = format_stereo_pose(items)
        poses.append(pose)
    return Ok(poses)

def read_stereo_pose_file(path: Path) -> Result[StereoPoses, str]:
    """ Read a stereo pose file from the Renav system. """
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
