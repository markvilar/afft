"""Module for camera processing task."""

import argparse


def process_cameras(arguments: list[str]) -> None:
    """Executor for camera processing task."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_config",
        type=Path,
        help="data configuration, i.e. files and directory paths",
    )
    namespace = parser.parse_args(arguments)

    raise NotImplementedError("process_cameras is not implemented")
