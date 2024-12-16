"""Module for message processing CLI."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Optional, TypeVar

import click
import polars as pl

from ..io import read_config, read_lines
from ..io.sql import create_endpoint, write_database
from ..services.sirius import Message, parse_message_lines
from ..utils.log import logger
from ..utils.result import Ok, Err, Result


type Topic = str
type Messages = Iterable[Message]
type MessageGroups = Mapping[Topic, Messages]


@click.group()
@click.pass_context
def message_cli(context: click.Context) -> None:
    """CLI group for invoking message processing tasks."""
    context.ensure_object(dict)


@message_cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("config", type=click.Path(exists=True))
@click.option("--database", type=str, help="destination database")
@click.option("--host", type=str, help="destination host")
@click.option("--port", type=int, help="destination port")
@click.option("--prefix", type=str, help="common prefix for exported message groups")
def parse_messages(
    source: str,
    config: str,
    database: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    prefix: Optional[str] = None,
) -> None:
    """CLI action for ingesting messages into a destination."""

    config: dict = read_config(Path(config)).unwrap()

    parse_result: Result[MessageGroups, str] = handle_message_parsing(source, config)
    if parse_result.is_err():
        logger.error(parse_result.err())
        return

    messages: MessageGroups = parse_result.ok()

    # Write to database if a database is provided
    if database:
        match handle_message_database_insertion(
            database, host, port, messages, config, prefix
        ):
            case Ok(None):
                pass
            case Err(error_message):
                logger.error(error_message)


def handle_message_parsing(
    source: str | Path, config: dict
) -> Result[MessageGroups, str]:
    """Handle parsing of messages."""

    lines: list[str] = read_lines(Path(source)).unwrap()

    topic_types: Optional[dict[Topic, str]] = config.get("message_maps")

    if topic_types is None:
        return Err("invalid config: missing topic types")

    # Read the message lines
    parsed_messages: MessageGroups = parse_message_lines(lines, topic_types)

    return Ok(parsed_messages)


def handle_message_database_insertion(
    database: str,
    host: str,
    port: int,
    message_groups: dict[str, Messages],
    config: dict[str, Any],
    prefix: Optional[str] = None,
) -> Result[None, str]:
    """Handle insertion of messages into a database."""

    table_names: Optional[dict[str, str]] = config.get("table_names")

    if table_names is None:
        return Err("invalid config: missing table names")

    if prefix is not None:
        table_names: dict[str, str] = {
            topic: f"{prefix}_{table_name}" for topic, table_name in table_names.items()
        }

    # Validate that every message group has an assigned table
    for group, messages in message_groups.items():
        if group not in table_names:
            return Err(f"missing table name for message group: {group}")

    # Group messages by database table name
    table_messages: dict[str, Messages] = dict()
    for group, messages in message_groups.items():
        table_name: str = table_names.get(group)

        if table_name not in table_messages:
            table_messages[table_name] = list()

        table_messages[table_name].extend(messages)

    # TODO: Validate that all table messages are the same type
    for table, messages in table_messages.items():
        pass

    # Convert messages to data frames
    dataframes: dict[str, pl.DataFrame] = {
        name: tabulate_messages(messages) for name, messages in table_messages.items()
    }

    logger.info("")
    logger.info("Writing database tables:")
    for name, dataframe in dataframes.items():
        logger.info(f" - {name}: {len(dataframe)}")
    logger.info("")

    # Create endpoint and insert
    match create_endpoint(database=database, host=host, port=port):
        case Ok(endpoint):
            _insert_results: dict[str, Result] = {
                table: write_database(endpoint, table, dataframe)
                for table, dataframe in dataframes.items()
            }
            # TODO: Handle insert results
        case Err(message):
            logger.error(message)


T: TypeVar = TypeVar("T")


def check_uniform_type(items: Iterable[T]) -> bool:
    """Returns true if all the items are the same type"""
    reference: type = type(items[0])
    is_same_type: list[bool] = [isinstance(item, reference) for item in items]
    return all(is_same_type)


def tabulate_messages(messages: Messages) -> pl.DataFrame:
    """Creates a data frame from a collection of messages. Assumes that
    the messages are of the same type or have the same fields."""
    return pl.DataFrame([message.to_dict() for message in messages])
