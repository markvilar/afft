"""Module with interfaces for processing of messages."""

from dataclasses import dataclass
from typing import Protocol


type Line = str


@dataclass
class HeadedMessage[Header, Body]:
    """Class representing a message composed of a header and body."""

    header: Header
    body: Body
