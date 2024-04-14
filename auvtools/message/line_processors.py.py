"""Processor functions for message lines."""

import re

from typing import Callable

# Interface for line processor
LineProcessor = Callable[[Line], Line]


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

    processors = [
        remove_subsequent_whitespaces,
        remove_ending_whitespaces,
        partial(replace_characters, target="[", replacement=""),
        partial(replace_characters, target="]", replacement=""),
        partial(replace_characters, target="\t", replacement=" "),
        partial(replace_characters, target=": ", replacement=":"),
    ]
