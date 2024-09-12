"""Module for CLI for working with message data."""

from pathlib import Path
from typing import Optional

import click

from ..io import read_config, read_lines
from ..services.sirius.message_interfaces import Message
from ..services.sirius.message_set import (
    MessageSet,
    build_message_set,
    parse_message_lines,
)
from ..utils.log import logger


@click.group()
@click.pass_context
def message_services(context: click.Context) -> None:
    """CLI group for message processing services."""
    context.ensure_object(dict)


@message_services.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("config", type=click.Path(exists=True))
@click.option("--database", type=str)
def parse_messages(source: str, config: str, database: Optional[str] = None) -> None:
    """CLI action for parsing messages from a source."""

    config: dict = read_config(Path(config)).unwrap()
    lines: list[str] = read_lines(Path(source)).unwrap()

    message_set: MessageSet = build_message_set(config.get("message_maps"))

    parsed_topics: dict[str, Message] = parse_message_lines(lines, message_set)

    for topic, messages in parsed_topics.items():
        logger.info(f"Topic: {topic}, messages: {len(messages)}")

    raise NotImplementedError("parse_messages is not implemented")
