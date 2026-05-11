"""
Loads environment variables from the .env file into os.environ on import.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE: Path = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(_ENV_FILE)

_TRUE_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: frozenset[str] = frozenset({"0", "false", "no", "off"})


def hasenv(key: str) -> bool:
    """Returns True if the environment variable is set."""
    return key in os.environ


def getenv(key: str, default: str | None = None) -> str | None:
    """Returns the value of an environment variable, or default if not set."""
    return os.getenv(key, default)


def requireenv(key: str) -> str:
    """Returns the value of an environment variable, or raises KeyError if not set."""
    value: str | None = os.getenv(key)
    if value is None:
        raise KeyError(f"missing environment variable: {key}")
    return value


def getenv_int(key: str, default: int | None = None) -> int | None:
    """Returns the value of an environment variable as an int.

    Raises ValueError if the value cannot be converted to int.
    """
    value: str | None = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"environment variable {key}={value!r} cannot be converted to int"
        )


def getenv_bool(key: str, default: bool | None = None) -> bool | None:
    """Returns the value of an environment variable as a bool.

    Accepts (case-insensitive): 1/true/yes/on for True, 0/false/no/off for False.
    Raises ValueError for any other value.
    """
    value: str | None = os.getenv(key)
    if value is None:
        return default
    normalised: str = value.strip().lower()
    if normalised in _TRUE_VALUES:
        return True
    if normalised in _FALSE_VALUES:
        return False
    raise ValueError(
        f"environment variable {key}={value!r} cannot be converted to bool"
    )
