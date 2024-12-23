"""Module for generating deployment descriptors."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from ...utils.result import Ok, Result


def parse_arguments(arguments: list[str]) -> Result[Namespace, str]:
    parser = ArgumentParser()
    parser.add_argument(
        "root",
        type=Path,
        help="root directory containing deployment directories",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output directory",
    )
    parser.add_argument("config", type=Path, help="config file path")
    parser.add_argument(
        "--prefix",
        type=str,
        required=False,
        default="",
        help="group prefix",
    )

    namespace: Namespace = parser.parse_args(arguments)

    return Ok(namespace)
