"""Module for message processing CLI."""

from pathlib import Path
from typing import Optional

import click

from ..io import read_config, read_lines
from ..io.database import create_engine

from ..services.sirius.message_interfaces import Message
from ..services.sirius.message_protocol import (
    MessageProtocol,
    build_message_protocol,
    parse_message_lines,
)

from ..tasks.ingest_messages import ingest_messages

from ..utils.log import logger


@click.group()
@click.pass_context
def message_cli(context: click.Context) -> None:
    """CLI group for invoking message processing tasks."""
    context.ensure_object(dict)


@message_cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination", type=click.Path(exists=True))
@click.argument("protocol", type=click.Path(exists=True))
@click.option("--prefix", type=str, help="prefix for exported data groups")
@click.option("--database", type=str, help="database name")
@click.option("--host", type=str, help="database host")
@click.option("--port", type=int, help="database port")
def parse_messages(
    source: str, 
    destination: str, 
    config: str, 
    prefix: Optional[str] = None,
) -> None:
    """CLI action for parsing messages from a source."""

    # TODO: Based on the destination - create / load destination endpoint

    config: dict = read_config(Path(config)).unwrap()
    lines: list[str] = read_lines(Path(source)).unwrap()

    message_protocol: MessageProtocol = build_message_protocol(config.get("message_maps"))

    parsed_topics: dict[str, Message] = parse_message_lines(lines, message_protocol)

    # TODO: Merge topics with the same message types?

    for topic, messages in parsed_topics.items():
        logger.info(f"Topic: {topic}, messages: {len(messages)}")


    ingest_messages

    raise NotImplementedError("parse_messages is not implemented")
