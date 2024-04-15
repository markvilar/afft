import os

from functools import partial
from pathlib import Path
from typing import Callable, Dict, List

from icecream import ic

from auvtools.io import read_json
from auvtools.transfer import (
    Endpoint,
    DirectoryQuery,
    FileQuery,
    QuerySetupFun,
    TransferAssignment,
)
from auvtools.utils import Logger


def create_queries(
    source: Endpoint,
    destination: Endpoint,
    references: Dict,
    logger: Logger = None,
) -> Dict[str, List[TransferAssignment]]:
    """
    Creates queries by setting up.

    Args:
     - references:          Reference data for setting up the queries
     - source:              Source endpoint
     - destination:         Destination endpoint
     - target_references:   Target entries in the references

    Return:
     - Dictionary with labelled collections of transfer assignments.
    """

    # FIXME: The source and destination is injected here to get their root
    # paths. Refactor the query setup so that it is not dependent on the source
    # and destination.

    # Create directory tree for destination
    directory_tree = dict()
    for group in references:
        directory_tree[group] = dict()
        for collection in references[group]:
            reference = references[group][collection]

            _, deployment = reference["root"].split("/")

            root_directory = destination.path / Path(group) / Path(deployment)

            dest_paths = {
                "bin": root_directory / "bin",
                "img": root_directory / "img",
                "log": root_directory / "log",
                "msg": root_directory / "msg",
            }

            # Create destination directories
            for label, path in dest_paths.items():
                os.makedirs(path, exist_ok=True)

            directory_tree[group][collection] = dest_paths

    # Set up queries
    transfers = dict()
    for group in references:
        for collection in references[group]:
            reference = references[group][collection]
            directories = directory_tree[group][collection]

            _, deployment = reference["root"].split("/")

            source_root = source.path / Path(group) / Path(deployment)

            directory_queries, file_queries = list(), list()

            # Set up directory queries
            keys = ["bin", "log", "msg"]
            for key in keys:
                query = DirectoryQuery(
                    source=source_root / reference["directories"][key],
                    destination=directories[key],
                )
                directory_queries.append(query)

            # Set up file queries
            file_query = FileQuery(
                source=source_root / "images",
                destination=directories["img"],
                include_files=[(label + "*") for label in reference["files"]],
            )
            file_queries.append(file_query)

            assignment = TransferAssignment(
                directory_queries=directory_queries,
                file_queries=file_queries,
            )

            transfers[collection] = assignment
    return transfers


def build_query_setup_function(
    source: Endpoint,
    destination: Endpoint,
    config: Dict,
    logger: Logger,
) -> QuerySetupFun:
    """
    Creates a function that prepares directories at a destination endpoint
    and sets up queries. The returned function is based on the contents of the
    provided configuration.
    """

    # Filter the references that are not in the target entries
    if "target_entries" in config["job"]:
        target_entries = [
            entry.strip() for entry in config["job"]["target_entries"].split(",")
        ]
        filter_by_keys = lambda keys: {x: references[x] for x in keys}
        reference_selection = filter_by_keys(target_entries)
    else:
        reference_selection = references

    # TODO: Set up directory validation

    # TODO: Consider splitting the directory creation and transfer setup.
    query_fun = partial(
        create_queries,
        source=source,
        destination=destination,
        references=reference_selection,
        logger=logger,
    )

    return query_fun
