"""Module for building protocols."""

from collections import Counter
from dataclasses import dataclass
from typing import Optional, Self

from .message_interfaces import Message, MessageParser
from .message_parsers import get_message_parser
from .concrete_messages import MessageHeader, get_message_type

from afft.utils.log import logger


@dataclass
class MessageProtocol:
    """Class representing a message set."""

    @dataclass
    class Item:
        """Class representing a message set item."""

        topic: str
        message_type: type
        message_parser: MessageParser

    items: dict[str, Item]

    def has_topic(self: Self, topic: str) -> bool:
        """Returns true if the protocol contains the topic."""
        return topic in self.items

    def get_topic(self: Self, topic: str) -> Optional[Item]:
        """Returns the item if the topic is in the protocol."""
        return self.items.get(topic)

    def list_topics(self: Self) -> list[str]:
        """Returns a list of topics in the message set."""
        return list(self.items.keys())


def build_message_protocol(topic_to_name: dict[str, str]) -> MessageProtocol:
    """Builds a protocol from a mapping from topic to a string representation of a message type."""

    items: list[MessageProtocol.Item] = list()
    for topic, name in topic_to_name.items():
        message_type: type = get_message_type(name)

        if not message_type:
            continue

        message_parser: Optional[MessageParser] = get_message_parser(
            message_type
        )

        if not message_type or not message_parser:
            continue

        items.append(MessageProtocol.Item(topic, message_type, message_parser))

    return MessageProtocol({item.topic: item for item in items})


def parse_message_lines(
    lines: list[str], topic_types: dict[str, str]
) -> dict[str, Message]:
    """Parses lines as message types in the given protocol."""

    protocol: MessageProtocol = build_message_protocol(topic_types)
    message_groups: dict[str, list[Message]] = dict()
    skipped: Counter[str] = Counter()
    failed: Counter[str] = Counter()

    for line in lines:
        header_parser: MessageParser | None = get_message_parser(MessageHeader)
        header: MessageHeader = header_parser(line)
        item: MessageProtocol.Item | None = protocol.get_topic(header.topic)

        if item is None:
            skipped[header.topic] += 1
            continue

        try:
            parsed_message: Message = item.message_parser(line)
        except ValueError:
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
