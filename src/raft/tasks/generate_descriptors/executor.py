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

from .data_types import QueryGroup, SelectionGroup, SupergroupQuery, SupergroupSelection


def list_subdirectories(root: Path) -> list[Path]:
    """Lists group directories by finding subdirectories within the root directory."""
    directories: list[Path] = sorted(
        [path for path in list_directory(root) if path.is_dir()]
    )
    return directories


def create_supergroup_query(root: Path, config: dict) -> SupergroupQuery:
    """Creates a supergroup query from config data."""

    children: list[Path] = list_subdirectories(root)
    execute_group_querys: list[QueryGroup] = list()

    # Create a query group for every child directory in the root directory
    for child in children:

        file_queries: list[FileQueryData] = list()

        for query_data in config["file_query"]:
            query_directory: Path = child / query_data["subdirectory"]
            file_queries.append(
                FileQueryData(
                    name=query_data["name"],
                    directory=query_directory,
                    pattern=query_data["pattern"],
                    recursive=query_data["recursive"],
                )
            )

        execute_group_querys.append(QueryGroup(name=child.name, queries=file_queries))

    return SupergroupQuery(name=config["name"], groups=execute_group_querys)


def query_files(query_data: FileQueryData) -> Result[FileSelection, str]:
    """Executes the file query and returns the result as a file selection."""
    search_result: Result[list[Path], str] = search_directory(
        query_data.directory,
        query_data.pattern,
        query_data.recursive,
    )

    if search_result.is_err():
        return search_result

    files: list[Path] = search_result.ok()
    return Ok(FileSelection(name=query_data.name, files=files))


def execute_group_query(group: QueryGroup) -> SelectionGroup:
    """TODO"""
    file_selections: list[FileSelection] = list()

    for file_query in group.queries:
        search_result: Result[FileSelection, str] = query_files(file_query)

        if search_result.is_err():
            logger.error(search_result.err())
            continue

        file_selection: FileSelection = search_result.ok()
        file_selection.files = sorted(file_selection.files)
        file_selections.append(file_selection)

    return SelectionGroup(name=group.name, file_selections=file_selections)


def execute_supergroup_query(supergroup: SupergroupQuery) -> SupergroupSelection:
    """TODO"""
    selections: list[SelectionGroup] = [
        execute_group_query(query) for query in supergroup.groups
    ]
    return SupergroupSelection(name=supergroup.name, groups=selections)


def make_selection_paths_relative(
    supergroup: SupergroupSelection, root: Path
) -> SupergroupSelection:
    """TODO"""

    for group in supergroup.groups:
        for selection in group.file_selections:
            selection.files = [file.relative_to(root) for file in selection.files]

    return supergroup


def export_supergroup_selection(
    supergroup: SupergroupSelection, output_file: Path
) -> None:
    """Exports a group selection by writing it to a TOML file."""

    data: dict = {supergroup.name: list()}

    for group in supergroup.groups:
        group_data = {"name": group.name}

        for file_selection in group.file_selections:
            group_data[file_selection.name] = [
                str(file) for file in file_selection.files
            ]

        data[supergroup.name].append(group_data)

    write_result: Result[Path, str] = write_toml(data, output_file)

    if write_result.is_err():
        logger.error(write_result.err())
    else:
        logger.info(f"wrote group descriptor: {output_file}")


def generate_group_descriptors(
    root: Path, output: Path, config: Path, prefix: str
) -> None:
    """Generate descriptors for a of deployments. The procedure searches for message
    and camera files for each deployment."""

    config: dict = read_toml(config).unwrap()

    # Create group queries for every entry in the config file
    for key in config["supergroup"]:
        query: SupergroupQuery = create_supergroup_query(
            root, config["supergroup"][key]
        )

        selection: SupergroupSelection = execute_supergroup_query(query)

        selection: SupergroupSelection = make_selection_paths_relative(selection, root)

        output_file: Path = output / f"{prefix}_file_descriptor.toml"

        export_supergroup_selection(selection, output_file)
