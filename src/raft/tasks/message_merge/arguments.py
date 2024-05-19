"""Module for message processing arguments."""

from argparse import ArgumentParser, Namespace, BooleanOptionalAction
from pathlib import Path

from result import Ok, Err, Result

def parse_arguments(arguments: list[str]) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "subtasks",
        type=Path,
        help="configuration file for message merge subtasks",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="input directory path",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output directory path",
    )

    namespace: Namespace = parser.parse_args(arguments)

    return Ok(namespace)
