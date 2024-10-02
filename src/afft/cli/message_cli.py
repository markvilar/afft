"""Module for message processing CLI."""

from pathlib import Path
from typing import Optional

import click

from ..io import read_config, read_lines
from ..services.sirius.message_interfaces import Message
from ..services.sirius.message_protocol import (
    MessageProtocol,
    build_message_protocol,
    parse_message_lines,
)
from ..utils.log import logger


@click.group()
@click.pass_context
def message_group(context: click.Context) -> None:
    """CLI group for invoking message processing tasks."""
    context.ensure_object(dict)


@message_group.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination", type=click.Path(exists=True))
@click.argument("config", type=click.Path(exists=True))
@click.option("--prefix", type=str, help="Prefix for exported data groups")
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

    raise NotImplementedError("parse_messages is not implemented")
