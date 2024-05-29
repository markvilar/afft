"""Module for executing group descriptor generation."""

from pathlib import Path
from typing import Callable

from result import Ok, Err, Result

from raft.filesystem import (
    list_directory,
    search_directory,
    FileQueryData,
    FileSelection,
)
from raft.io import read_toml, write_toml
from raft.utils.log import logger

from .data_types import QueryItem, SelectionItem, MetafileGenerationContext


def list_subdirectories(root: Path) -> list[Path]:
    """Lists group directories by finding subdirectories within the root directory."""
    directories: list[Path] = sorted(
        [path for path in list_directory(root) if path.is_dir()]
    )
    return directories


def get_target_directories(root: Path, config: dict) -> list[Path]:
    """Returns target directories by listing the subdirectories of the root directory."""
    children: list[Path] = list_subdirectories(root)
    return children


def generate_target_name(target: Path, prefix: str) -> str:
    """Generates a target name by prepending the prefix to the directory name."""
    return f"{prefix}_{target.name}"


def create_file_query(config: dict) -> FileQueryData:
    """Creates a file query from a configuration file entry."""
    return FileQueryData(**config)


def create_query_item(
    name: str, directory: Path, query_data: FileQueryData
) -> QueryItem:
    """Creates a collection of query items from target directories and a file query configuration."""
    return QueryItem(name, directory, query_data)


def execute_query(query_item: QueryItem) -> Result[SelectionItem, str]:
    """Returns a selection of paths by querying the target directory."""

    search_result: Result[list[Path], str] = search_directory(
        query_item.directory,
        query_item.query_data.pattern,
        query_item.query_data.recursive,
    )

    if search_result.is_err():
        return search_result

    selected_files: list[Path] = search_result.ok()

    selection: SelectionItem = SelectionItem(
        name=query_item.name,
        files=selected_files,
    )

    return Ok(selection)


def make_selection_paths_relative(
    selection: SelectionItem, reference: Path
) -> SelectionItem:
    """Update the paths of a file selection to be relative to the reference."""
    selection.files = [file.relative_to(reference) for file in selection.files]
    return selection


def serialize_selection(selection: SelectionItem) -> dict:
    """Serializes selection items to a dictionary."""
    return {"name": selection.name, "files": [str(file) for file in selection.files]}

    return (data, output_file)


def generate_metafiles(context: MetafileGenerationContext, config: Path) -> None:
    """Generate descriptors for a of deployments. The procedure searches for message
    and camera files for each deployment."""

    config: dict = read_toml(config).unwrap()

    # Find directories to query
    target_directories: list[Path] = get_target_directories(
        context.root_directory, config["targets"]
    )

    # Assign names to targets based on directory name and prefix
    targets: dict[str, Path] = dict()
    for directory in target_directories:
        name: str = generate_target_name(directory, context.prefix)
        targets[name] = directory

    serialized_groups: dict[str, list] = dict()

    for name, group_config in config["groups"].items():

        file_query_data: FileQueryData = create_file_query(group_config["file_query"])

        queries: list[QueryItem] = list()
        for target_name, target_directory in targets.items():
            queries.append(
                create_query_item(target_name, target_directory, file_query_data)
            )

        query_results: list[Result[SelectionItem, str]] = [
            execute_query(query) for query in queries
        ]

        # Acquire the selections from successful queries
        selections: list[SelectionItem] = [
            result.ok() for result in query_results if result.is_ok()
        ]

        # Make file paths in selection relative to the root directory
        selections: list[SelectionItem] = [
            make_selection_paths_relative(selection, context.root_directory)
            for selection in selections
        ]

        # Serialize selection data to write to file
        serialized_groups[name] = [
            serialize_selection(selection) for selection in selections
        ]

    output_file: Path = context.output_directory / f"{context.prefix}_metafile.toml"
    write_result: Result[Path, str] = write_toml(serialized_groups, output_file)

    if write_result.is_err():
        logger.error(write_result.err())
    else:
        logger.info(f"wrote metafile: {output_file}")
