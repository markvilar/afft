"""Module for message facade."""

from collections.abc import Callable
from typing import Generic, Protocol, TypeVar


Header: TypeVar = TypeVar("Header")
Body: TypeVar = TypeVar("Body")


class Message(Protocol, Generic[Header, Body]):
    """Class representing a message interface."""

    @property
    def header_type(self) -> type: ...

    @property
    def body_type(self) -> type: ...

    @property
    def header(self) -> Header: ...

    @property
    def body(self) -> Body: ...


type MessageParser = Callable[[str], Message]
