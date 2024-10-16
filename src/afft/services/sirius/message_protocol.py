"""Module for building protocols."""

from dataclasses import dataclass
from typing import Optional, Self

from .message_interfaces import Message, MessageParser
from .message_parsers import get_message_parser
from .concrete_messages import MessageHeader, get_message_type

from afft.utils.log import logger
from afft.utils.result import Ok, Err


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

        message_parser: Optional[MessageParser] = get_message_parser(message_type)

        if not message_type or not message_parser:
            continue

        items.append(MessageProtocol.Item(topic, message_type, message_parser))

    return MessageProtocol({item.topic: item for item in items})


def parse_message_lines(
    lines: list[str], topic_types: dict[str, str]
) -> dict[str, Message]:
    """Parses lines as message types in the given protocol."""

    protocol: MessageProtocol = build_message_protocol(topic_types)
    parsed: dict[str, list[Message]] = dict()

    for line in lines:
        header_parser: Optional[MessageParser] = get_message_parser(MessageHeader)

        header: MessageHeader = header_parser(line).unwrap()

        item: Optional[MessageProtocol.Item] = protocol.get_topic(header.topic)

        if not item:
            continue

        # Parse message line and handle result
        match item.message_parser(line):
            case Ok(message):
                if header.topic not in parsed:
                    parsed[header.topic] = list()
                parsed[header.topic].append(message)
            case Err(error):
                logger.warning(error)

    return parsed
