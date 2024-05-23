"""Module with data types for the file descriptor generation."""

from dataclasses import dataclass
from pathlib import Path

from raft.filesystem import FileQueryData, FileSelection


@dataclass
class QueryGroup:
    """Class representing a group of file queries."""

    name: str
    queries: list[FileQueryData]


@dataclass
class SupergroupQuery:
    """Class representing a supergroup of query groups."""

    name: str
    groups: list[QueryGroup]


@dataclass
class SelectionGroup:
    """Class representing a group of file selections."""

    name: str
    file_selections: list[FileSelection]


@dataclass
class SupergroupSelection:
    """Class representing a supergroup of selection groups."""

    name: str
    groups: list[SelectionGroup]
