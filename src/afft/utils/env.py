"""Module for environment variables."""

from pathlib import Path
from typing import Any

import dotenv


# Set default env file path to .env file in project root
DEFAULT_ENV_FILE: Path = Path(__file__).resolve().parents[3] / ".env"


def get_default_path() -> Path:
    """Returns the path of the default .env file."""
    return DEFAULT_ENV_FILE


def env_values() -> dict[str, Any]:
    """Returns the values in a environment file."""
    return dotenv.dotenv_values(DEFAULT_ENV_FILE)


def get_env_value(key: str) -> Any | None:
    """Returns the environment value for a given key."""
    return dotenv.dotenv_values(DEFAULT_ENV_FILE).get(key)
