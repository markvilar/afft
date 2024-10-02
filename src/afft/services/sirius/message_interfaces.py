"""Module for message facade."""

from collections.abc import Callable
from typing import Any, Generic, Protocol, Self, TypeVar


Header: TypeVar = TypeVar("Header")
Body: TypeVar = TypeVar("Body")


class Message(Protocol, Generic[Header, Body]):
    """Class representing a message interface."""

    @property
    def header_type(self) -> type:
        """Returns the header type for the message."""
        ...

    @property
    def body_type(self) -> type:
        """Returns the body type for the message."""
        ...

    @property
    def header(self) -> Header:
        """Returns the header instance of the message."""
        ...

    @property
    def body(self) -> Body:
        """Returns the body instance of the message."""
        ...

    def to_dict(self: Self) -> dict[str, Any]:
        """Returns a dictionary of the message fields."""
        ...


type MessageParser = Callable[[str], Message]
