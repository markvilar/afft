"""Module for CLI for working with message data."""

from typing import Optional

import click


@click.group()
@click.pass_context
def message_services(context: click.Context) -> None:
    """CLI group for message processing services."""
    context.ensure_object(dict)


@message_services.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--database", type=str)
def parse_messages(source: str, database: Optional[str] = None) -> None:
    """CLI action for parsing messages from a source."""

    raise NotImplementedError("parse_messages is not implemented")
