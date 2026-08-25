"""Module for message facade."""

from collections.abc import Callable
from typing import Any, Generic, Protocol, Self, TypeVar


Header = TypeVar("Header", covariant=True)
Payload = TypeVar("Payload", covariant=True)

type Topic = str
type MessageTypeName = str


class MessageParseError(ValueError):
    """Raised when a log line cannot be parsed as a message."""


class Message(Protocol, Generic[Header, Payload]):
    """Class representing a message interface."""

    @property
    def header(self) -> Header:
        """Returns the header instance of the message."""
        ...

    @property
    def payload(self) -> Payload:
        """Returns the payload instance of the message."""
        ...

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dictionary of the message fields."""
        ...


type MessageParser = Callable[[str], Message[Any, Any]]
