"""Reader and writer for the deployment descriptors TOML file."""

import msgspec

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .descriptor_types import DeploymentDescriptor


def read_deployment_descriptors(path: Path) -> list[DeploymentDescriptor]:
    """
    Read deployment descriptors from a deployments TOML file.

    Arguments
    ---------
    path: Path to the deployments TOML file.

    Returns
    -------
    List of deployment descriptors.
    """
    raw: dict[str, Any] = read_config(path)
    return [
        DeploymentDescriptor.model_validate(entry)
        for entry in raw.get("deployments", [])
    ]


def write_deployment_descriptors(
    path: Path,
    descriptors: list[DeploymentDescriptor],
) -> None:
    """
    Write deployment descriptors to a deployments TOML file.

    Unfilled curated slots are omitted rather than written as null: TOML has no
    null literal, and the ``None`` defaults restore them on read.

    The document is emitted here rather than by ``msgspec.toml.encode``, which
    delegates to ``tomli_w`` and so can neither write dotted keys nor be kept
    from collapsing short tables into inline ones. Two properties follow that
    the encoder does not offer:

    - A sensor's ``identity`` and ``extrinsics`` are written as dotted keys
      within its own block — ``identity.label``, ``extrinsics.locx`` — rather
      than as sub-table headers, keeping one sensor to one block.
    - Every table gets a section header, and a sensor roster is always an
      array-of-tables. The layout therefore follows the schema, not which
      curated slots a given deployment happens to have filled.

    Arguments
    ---------
    path: Path to write the deployments TOML file.
    descriptors: Deployment descriptors to serialize.
    """
    blocks: list[str] = []
    for descriptor in descriptors:
        blocks.extend(
            _format_table(
                "deployments",
                descriptor.model_dump(mode="python", exclude_none=True),
                array_entry=True,
            )
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def _format_table(
    name: str,
    table: dict[str, Any],
    *,
    array_entry: bool = False,
    dotted_children: bool = False,
) -> list[str]:
    """
    Format a table as a list of TOML blocks, one per section header.

    Arguments
    ---------
    name: Fully qualified table name, written as the section header.
    table: The table's contents.
    array_entry: Write the header as an array-of-tables entry.
    dotted_children: Write nested tables as dotted keys in this table's own
        block instead of as sub-table headers.

    Returns
    -------
    The table's blocks, to be joined by blank lines.
    """
    lines: list[str] = [f"[[{name}]]" if array_entry else f"[{name}]"]
    tables: list[tuple[str, dict[str, Any]]] = []
    rosters: list[tuple[str, list[dict[str, Any]]]] = []

    for key, value in table.items():
        if isinstance(value, dict):
            if dotted_children:
                lines.extend(_format_dotted_pairs(key, value))
            else:
                tables.append((key, value))
        elif _is_table_array(value):
            rosters.append((key, value))
        else:
            lines.append(_format_pair(key, value))

    blocks: list[str] = ["\n".join(lines)]
    for key, nested_table in tables:
        blocks.extend(_format_table(f"{name}.{key}", nested_table))
    for key, roster in rosters:
        for entry in roster:
            blocks.extend(
                _format_table(
                    f"{name}.{key}",
                    entry,
                    array_entry=True,
                    dotted_children=True,
                )
            )

    return blocks


def _is_table_array(value: Any) -> bool:
    """Whether a value is a non-empty array of tables."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(entry, dict) for entry in value)
    )


def _format_dotted_pairs(prefix: str, table: dict[str, Any]) -> list[str]:
    """
    Format a nested table as dotted-key lines, recursing through nested
    dicts so every leaf value becomes its own ``prefix.path = value`` line.

    Arguments
    ---------
    prefix: Dotted key path built so far.
    table: The table's contents.

    Returns
    -------
    One dotted-key line per leaf value.
    """
    lines: list[str] = []
    for key, value in table.items():
        if isinstance(value, dict):
            lines.extend(_format_dotted_pairs(f"{prefix}.{key}", value))
        else:
            lines.append(f"{prefix}.{_format_pair(key, value)}")
    return lines


def _format_pair(key: str, value: Any) -> str:
    """
    Format one key/value pair.

    The value is handed to the TOML encoder so that strings, floats, datetimes,
    and arrays render exactly as they do elsewhere in the package.
    """
    return msgspec.toml.encode({key: value}).decode().rstrip("\n")
