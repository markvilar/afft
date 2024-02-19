""" Functionality for matching of cameras. """
from typing import Dict, List

from .camera import Camera

Cameras = List[Camera]

def match_cameras_by_label(
    cameras: Cameras, 
    targets: List[str],
) -> Dict[str, Camera]:
    """ Matches cameras with a list of targets based on their index. """
    matches = [ camera for camera in cameras if camera.label in targets]
    return matches
