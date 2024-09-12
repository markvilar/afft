"""Module for building protocols."""

from dataclasses import dataclass
from typing import Optional, Self

from .message_interfaces import Message, MessageParser
from .message_parsers import parse_message_header, MESSAGE_TYPE_TO_PARSER
from .message_types import AuvMessageHeader, MESSAGE_NAME_TO_TYPE


@dataclass
class MessageSet:
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


def build_message_set(topic_to_name: dict[str, str]) -> MessageSet:
    """Builds a protocol from a mapping from topic to a string representation of a message type."""

    items: list[MessageSet.Item] = list()
    for topic, name in topic_to_name.items():
        message_type: type = MESSAGE_NAME_TO_TYPE.get(name)

        if not message_type:
            continue

        message_parser: MessageParser = MESSAGE_TYPE_TO_PARSER.get(message_type)

        if not message_type or not message_parser:
            continue

        items.append(MessageSet.Item(topic, message_type, message_parser))

    return MessageSet({item.topic: item for item in items})


def parse_message_lines(
    lines: list[str], message_set: MessageSet
) -> dict[str, Message]:
    """Parses lines"""

    parsed: dict[str, list[Message]] = dict()

    for line in lines:
        header: AuvMessageHeader = parse_message_header(line).unwrap()

        item: Optional[MessageSet.Item] = message_set.get_topic(header.topic)

        if not item:
            continue

        message: Message = item.message_parser(line).unwrap()
        if header.topic not in parsed:
            parsed[header.topic] = list()

        parsed[header.topic].append(message)

    return parsed
