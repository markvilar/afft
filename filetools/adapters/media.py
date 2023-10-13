from argparse import ArgumentParser
from pathlib import Path

def add_directory_cleanup_arguments(parser: ArgumentParser):
    """ Add directory clean up arguments to an argument parser. """
    parser.add_argument("--include",
        type=Path,
        help="paths to preserve while doing to the cleanup",
    )
    parser.add_argument("--exclude",
        type=Path,
        help="paths to preserve while doing to the cleanup",
    )
    parser.add_argument("--source",
        type=Path,
        required=True,
        help="the directory path to clean",
    )
