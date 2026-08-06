"""Module for building message parser registries."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Self

from .message_interfaces import (
    Message,
    MessageParseError,
    MessageParser,
    MessageTypeName,
    Topic,
)
from .message_parsers import get_message_parser, parse_message_header
from .message_types import MessageHeader, get_message_type

from afft.utils.log import logger


@dataclass(frozen=True)
class MessageParserRegistryEntry:
    """
    Attributes
    ----------
    topic: Message topic string.
    message_type: Resolved message type for the topic.
    message_parser: Parser for the message type.
    """

    topic: Topic
    message_type: type
    message_parser: MessageParser


@dataclass
class MessageParserRegistry:
    """
    Attributes
    ----------
    entries: Registered entries.
    """

    entries: list[MessageParserRegistryEntry] = field(default_factory=list)

    def register(self: Self, entry: MessageParserRegistryEntry) -> None:
        """Register an entry, raising if its topic is already registered."""
        if self.has_topic(entry.topic):
            raise ValueError(f"topic already registered: {entry.topic}")
        self.entries.append(entry)

    def has_topic(self: Self, topic: Topic) -> bool:
        """Returns true if the topic is registered."""
        return any(entry.topic == topic for entry in self.entries)

    def get_topic(
        self: Self, topic: Topic
    ) -> MessageParserRegistryEntry | None:
        """Returns the entry for the topic, if registered."""
        return next(
            (entry for entry in self.entries if entry.topic == topic), None
        )

    def list_topics(self: Self) -> list[Topic]:
        """Returns the registered topics."""
        return [entry.topic for entry in self.entries]

    @property
    def topic_to_parser(self: Self) -> dict[Topic, MessageParser]:
        """Returns a mapping from topic to parser."""
        return {entry.topic: entry.message_parser for entry in self.entries}

    @property
    def topic_to_type(self: Self) -> dict[Topic, type]:
        """Returns a mapping from topic to message type."""
        return {entry.topic: entry.message_type for entry in self.entries}


def build_message_parser_registry(
    topic_to_name: dict[Topic, MessageTypeName],
) -> MessageParserRegistry:
    """Builds a registry from a mapping of topic to message type name."""
    registry = MessageParserRegistry()

    for topic, name in topic_to_name.items():
        message_type = get_message_type(name)
        if message_type is None:
            continue

        message_parser = get_message_parser(message_type)
        if message_parser is None:
            continue

        registry.register(
            MessageParserRegistryEntry(topic, message_type, message_parser)
        )

    return registry


def parse_message_lines(
    lines: list[str], registry: MessageParserRegistry
) -> dict[str, list[Message[Any, Any]]]:
    """Parses lines as message types in the given registry."""

    message_groups: dict[str, list[Message[Any, Any]]] = dict()
    skipped: Counter[str] = Counter()
    failed: Counter[str] = Counter()

    for line in lines:
        header: MessageHeader = parse_message_header(line)
        entry: MessageParserRegistryEntry | None = registry.get_topic(
            header.topic
        )

        if entry is None:
            skipped[header.topic] += 1
            continue

        try:
            parsed_message: Message[Any, Any] = entry.message_parser(line)
        except MessageParseError:
            failed[header.topic] += 1
            continue

        if header.topic not in message_groups:
            message_groups[header.topic] = list()
        message_groups[header.topic].append(parsed_message)

    if skipped:
        logger.warning(
            "Skipped messages with no protocol item ({} topics, {} total):{}".format(
                len(skipped),
                sum(skipped.values()),
                "".join(
                    f"\n  {topic}: {count}"
                    for topic, count in sorted(skipped.items())
                ),
            )
        )

    if failed:
        logger.warning(
            "Failed to parse messages ({} topics, {} total):{}".format(
                len(failed),
                sum(failed.values()),
                "".join(
                    f"\n  {topic}: {count}"
                    for topic, count in sorted(failed.items())
                ),
            )
        )

    return message_groups
