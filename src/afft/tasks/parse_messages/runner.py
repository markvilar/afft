"""Runner for the message parsing task."""

from collections.abc import Iterable, Mapping
from pathlib import Path

import polars as pl

import afft.database as db
import afft.io as io
import afft.sirius as sirius
import afft.utils.env as env

from afft.utils.log import logger

from .types import ParseMessageCommand, ParseMessageConfig


type Topic = str
type Messages = Iterable[sirius.Message]
type MessageGroups = Mapping[Topic, Messages]


def run_parse_messages(command: ParseMessageCommand) -> None:
    """Parse messages from source file and optionally ingest into a database
    and/or export to CSV files."""
    raw_config: dict = io.read_config(command.config_file)
    config = _load_config(raw_config)

    messages = _parse_messages(command.source_file, config)
    dataframes = _build_dataframes(messages, config, command.prefix)

    if command.database:
        _insert_dataframes(command, dataframes)

    if command.output_dir:
        _export_dataframes(command.output_dir, dataframes)


def _load_config(raw: dict) -> ParseMessageConfig:
    message_maps = raw.get("message_maps")
    table_names = raw.get("table_names")

    if message_maps is None:
        raise ValueError("invalid config: missing message_maps")
    if table_names is None:
        raise ValueError("invalid config: missing table_names")

    return ParseMessageConfig(message_maps=message_maps, table_names=table_names)


def _parse_messages(
    source_file: Path, config: ParseMessageConfig
) -> MessageGroups:
    lines: list[str] = io.read_lines(source_file)
    return sirius.parse_message_lines(lines, config.message_maps)


def _build_dataframes(
    message_groups: MessageGroups,
    config: ParseMessageConfig,
    prefix: str | None,
) -> dict[str, pl.DataFrame]:
    table_names = dict(config.table_names)

    if prefix is not None:
        table_names = {
            topic: f"{prefix}_{name}"
            for topic, name in table_names.items()
        }

    for group in message_groups:
        if group not in table_names:
            raise ValueError(f"missing table name for message group: {group}")

    table_messages: dict[str, list] = {}
    for group, messages in message_groups.items():
        table_name = table_names[group]
        if table_name not in table_messages:
            table_messages[table_name] = []
        table_messages[table_name].extend(messages)

    return {
        name: pl.DataFrame([m.to_dict() for m in messages])
        for name, messages in table_messages.items()
    }


def _insert_dataframes(
    command: ParseMessageCommand,
    dataframes: dict[str, pl.DataFrame],
) -> None:
    assert "PG_USERNAME" in env.env_values(), (
        "missing environment key: PG_USERNAME"
    )
    assert "PG_PASSWORD" in env.env_values(), (
        "missing environment key: PG_PASSWORD"
    )

    engine: db.Engine | str = db.create_engine(
        database=command.database,
        host=command.host,
        port=command.port,
        username=env.get_env_value("PG_USERNAME"),
        password=env.get_env_value("PG_PASSWORD"),
    )

    assert isinstance(engine, db.Engine), (
        f"error while connecting to engine: {engine}"
    )

    logger.info("Writing database tables:")
    for name, dataframe in dataframes.items():
        logger.info(f" - {name}: {len(dataframe)}")
        db.write_database_table(engine, name, dataframe)


def _export_dataframes(
    output_dir: Path,
    dataframes: dict[str, pl.DataFrame],
) -> None:
    if not output_dir.is_dir():
        raise ValueError(f"output directory does not exist: {output_dir}")

    logger.info("Exporting tables to CSV:")
    for name, dataframe in dataframes.items():
        dest = output_dir / f"{name}.csv"
        dataframe.write_csv(dest)
        logger.info(f" - {name}: {len(dataframe)} rows -> {dest}")
