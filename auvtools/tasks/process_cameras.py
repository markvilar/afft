"""Module for camera processing task."""

import argparse

from typing import List


def process_cameras(arguments: List[str]) -> None:
    """Executor for camera processing task."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_config",
        type=Path,
        help="data configuration, i.e. files and directory paths",
    )
    namespace = parser.parse_args(arguments)
    raise NotImplementedError
