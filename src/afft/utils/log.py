"""Module for logging functionality."""

import sys

from collections import OrderedDict

import loguru
import dotenv

from .time import get_time_string

LOG_DIRECTORY_KEY: str = "LOG_DIRECTORY"
LOG_LEVEL: str = "DEBUG"

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <4}</level>"
    " | <cyan>Line {line: >4} ({file}):</cyan> <b>{message}</b>"
)


def init_logger() -> None:
    """Initializes the logger."""

    env_values: OrderedDict = dotenv.dotenv_values(".env")

    if LOG_DIRECTORY_KEY in env_values:
        directory: str = env_values[LOG_DIRECTORY_KEY]
    else:
        directory: str = "./log"

    datetime: str = get_time_string("YYYYMMDD_HHmmss")
    log_file: str = f"{directory}/{datetime}.log"

    # Clear default logger
    loguru.logger.remove()

    # Add custom sinks
    loguru.logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    loguru.logger.add(
        log_file,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )


logger = loguru.logger
