"""Module for logging functions."""

import sys

from dotenv import dotenv_values
from loguru import logger

from .time import get_time_string

LOG_DIRECTORY = "LOG_DIRECTORY"
LOG_LEVEL = "DEBUG"

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <4}</level>"
    " | <cyan>Line {line: >4} ({file}):</cyan> <b>{message}</b>"
)


def init_logger() -> None:
    """Initializes the logger."""
    directory: str = dotenv_values(LOG_DIRECTORY)
    datetime: str = get_time_string("YYYYMMDD_HHmmss")
    log_file: str = f"{directory}/{datetime}.log"

    # Clear default logger
    logger.remove()

    # Add custom sinks
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    logger.add(
        log_file,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )
