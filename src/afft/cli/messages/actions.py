"""Actions for message processing CLI commands."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Optional, TypeVar

import polars as pl

import afft.database as db
import afft.io as io
import afft.sirius as sirius
import afft.utils.env as env

from afft.utils.log import logger


type Topic = str
type Messages = Iterable[sirius.Message]
type MessageGroups = Mapping[Topic, Messages]


def dispatch_parse_messages(
    source: str | Path,
    config: str | Path,
    database: str | None = None,
    host: str | None = None,
    port: int | None = None,
    prefix: str | None = None,
) -> None:
    """Parse messages and optionally ingest them into a database."""
    config: dict = io.read_config(Path(config))
    messages: MessageGroups = _parse_messages(source, config)

    if database:
        _insert_messages(database, host, port, messages, config, prefix)


def _parse_messages(
    source: str | Path, config: dict
) -> MessageGroups:
    lines: list[str] = io.read_lines(Path(source))
    topic_types: Optional[dict[Topic, str]] = config.get("message_maps")

    if topic_types is None:
        raise ValueError("invalid config: missing topic types")

    return sirius.parse_message_lines(lines, topic_types)


def _insert_messages(
    database: str,
    host: str,
    port: int,
    message_groups: dict[str, Messages],
    config: dict[str, Any],
    prefix: str | None = None,
) -> None:
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
        table_names = {
            topic: f"{prefix}_{table_name}"
            for topic, table_name in table_names.items()
        }

    for group, messages in message_groups.items():
        if group not in table_names:
            raise ValueError(f"missing table name for message group: {group}")

    table_messages: dict[str, Messages] = dict()
    for group, messages in message_groups.items():
        table_name: str = table_names.get(group)

        if table_name not in table_messages:
            table_messages[table_name] = list()

        table_messages[table_name].extend(messages)

    dataframes: dict[str, pl.DataFrame] = {
        name: _tabulate_messages(messages)
        for name, messages in table_messages.items()
    }

    logger.info("")
    logger.info("Writing database tables:")
    for name, dataframe in dataframes.items():
        logger.info(f" - {name}: {len(dataframe)}")
    logger.info("")

    _insert_results: dict[str, int] = {
        table: db.write_database_table(engine, table, dataframe)
        for table, dataframe in dataframes.items()
    }


T: TypeVar = TypeVar("T")


def _tabulate_messages(messages: Messages) -> pl.DataFrame:
    return pl.DataFrame([message.to_dict() for message in messages])
