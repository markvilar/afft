"""Module for message processing CLI."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Optional, TypeVar

import click
import polars as pl

import afft.database as db
import afft.io as io
import afft.sirius as sirius
import afft.utils.env as env

from afft.utils.log import logger


type Topic = str
type Messages = Iterable[sirius.Message]
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
@click.option(
    "--prefix", type=str, help="common prefix for exported message groups"
)
def parse_messages(
    source: str,
    config: str,
    database: str | None = None,
    host: str | None = None,
    port: int | None = None,
    prefix: str | None = None,
) -> None:
    """CLI action for ingesting messages into a destination."""

    config: dict = io.read_config(Path(config)).unwrap()
    messages: MessageGroups = handle_message_parsing(source, config)

    # Write to database if a database is provided
    if database:
        handle_message_database_insertion(
            database, host, port, messages, config, prefix
        )


def handle_message_parsing(source: str | Path, config: dict) -> MessageGroups:
    """Handle parsing of messages."""
    lines: list[str] = io.read_lines(Path(source)).unwrap()
    topic_types: Optional[dict[Topic, str]] = config.get("message_maps")

    if topic_types is None:
        raise ValueError("invalid config: missing topic types")

    # Read the message lines
    parsed_messages: MessageGroups = sirius.parse_message_lines(
        lines, topic_types
    )

    return parsed_messages


def handle_message_database_insertion(
    database: str,
    host: str,
    port: int,
    message_groups: dict[str, Messages],
    config: dict[str, Any],
    prefix: str | None = None,
) -> None:
    """Handle insertion of messages into a database."""

    assert "PG_USERNAME" in env.env_values(), (
        "missing environment key: PG_USERNAME"
    )
    assert "PG_PASSWORD" in env.env_values(), (
        "missing environment key: PG_PASSWORD"
    )

    engine: db.Engine | str = db.create_engine(
        database=database,
        host=host,
        port=port,
        username=env.get_env_value("PG_USERNAME"),
        password=env.get_env_value("PG_PASSWORD"),
    )

    assert isinstance(engine, db.Engine), (
        f"error while connecting to engine: {engine}"
    )

    table_names: dict[str, str] | None = config.get("table_names")

    if table_names is None:
        raise ValueError("invalid config: missing table names")

    if prefix is not None:
        table_names: dict[str, str] = {
            topic: f"{prefix}_{table_name}"
            for topic, table_name in table_names.items()
        }

    # Validate that every message group has an assigned table
    for group, messages in message_groups.items():
        if group not in table_names:
            raise ValueError(f"missing table name for message group: {group}")

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
        name: tabulate_messages(messages)
        for name, messages in table_messages.items()
    }

    logger.info("")
    logger.info("Writing database tables:")
    for name, dataframe in dataframes.items():
        logger.info(f" - {name}: {len(dataframe)}")
    logger.info("")

    # Create endpoint and insert
    _insert_results: dict[str, int] = {
        table: db.write_database_table(engine, table, dataframe)
        for table, dataframe in dataframes.items()
    }


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
