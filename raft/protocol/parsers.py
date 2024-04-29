"""Module for parsing of message data types."""

import re

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Callable, Tuple, Generic, TypeVar

from loguru import logger
from result import Ok, Err, Result

from raft.message.interfaces import Line

from .data_types import AuvMessageHeader
from .data_parsers import (
    parse_image_message_v1,
    parse_image_message_v2,
    parse_thruster_message,
    parse_battery_message,
)


type HeaderParseResult = Result[AuvMessageHeader, str]


T = TypeVar("T")


@dataclass
class ParsedLine:
    data: T
    line: str


@dataclass
class SplitLine:
    header: str
    body: str


def split_header_and_body_strings(line: Line) -> Result[SplitLine, str]:
    """Splits a message line into the header and body substrings."""
    pattern = re.compile(
        r"""
        ^(?P<topic>.*?):                # start, topic, colon
        \s(?P<timestamp>\d+\.\d+)\s+    # whitespace, timestamp
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to match header: {line}")

    start, end = match.start(), match.end()

    header = line[start:end]
    body = line.replace(header, "")

    return Ok(SplitLine(header=header, body=body))


def parse_message_header(line: Line) -> HeaderParseResult:
    """Parses the header from a message line."""

    pattern = re.compile(
        r"""
        ^(?P<topic>.*?):                # start, topic, colon
        \s(?P<timestamp>\d+\.\d+)\s+    # whitespace, timestamp
        """,
        re.VERBOSE,
    )

    match = pattern.match(line)

    if not match:
        return Err(f"failed to parse header: {line}")

    header = AuvMessageHeader(
        topic=str(match["topic"]),
        timestamp=float(match["timestamp"]),
    )

    return Ok(header)


type MessageBodyParser = Callable[[AuvMessageHeader, Line], Any]


def parse_message(line: Line, parsers: Dict[str, MessageBodyParser]) -> None:
    """Parses a message by dispatching based on the header information."""

    split: SplitLine = split_header_and_body_strings(line).unwrap()

    header = parse_message_header(split.header).unwrap()

    if not header.topic in parsers:
        return Err(f"no parser for topic: {header.topic}")

    body = parsers[header.topic](header, split.body).unwrap()

    # TODO: Create a dataclass to contain these
    message = {
        "header" : header,
        "body" : body,
    }
