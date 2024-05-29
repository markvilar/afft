"""Processor functions for message lines."""

import re

from functools import partial
from typing import Callable, List

# Interface for line processor
type LineProcessor = Callable[[str], str]


def remove_subsequent_whitespaces(string: str) -> str:
    """Removes subsequent whitespaces from a string."""
    return re.sub(" +", " ", string)


def remove_ending_whitespaces(string: str) -> str:
    """Removes leading and trailing whitespaces from a string."""
    return string.strip()


def remove_brackets(string: str) -> str:
    """Removes square bracket characters from a string."""
    return string.replace("[", "").replace("]", "")


def replace_characters(string: str, target: str, replacement: str) -> str:
    """Replaces tab characters from a string."""
    return string.replace(target, replacement)


def condense_key_value_pairs(string: str) -> str:
    """Removes whitespace after semicolons to condense key-value pairs."""
    return string.replace(": ", ":")


def default_line_processors() -> List[LineProcessor]:
    """Returns the default message line processors."""

    return [
        remove_subsequent_whitespaces,
        remove_ending_whitespaces,
        partial(replace_characters, target="\t", replacement=" "),
    ]


def process_message_lines(
    lines: List[str],
    processors: List[LineProcessor] = default_line_processors(),
) -> List[str]:
    """Applies the processors to the message lines."""

    processed_lines: List[str] = list()
    for line in lines:
        processed_line = line
        for processor in processors:
            processed_line = processor(processed_line)

        processed_lines.append(processed_line)

    return processed_lines
