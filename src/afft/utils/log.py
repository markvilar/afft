"""Module for logging functionality."""

import sys

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import loguru

from afft.environment import EnvironmentDirectories

from .time import get_time_string

LOG_LEVEL: str = "DEBUG"

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <4}</level>"
    " | <cyan>Line {line: >4} ({file}):</cyan> <b>{message}</b>"
)

_console_logging_suppressed: bool = False


def init_logger() -> None:
    """Initializes the logger."""

    directory: Path = EnvironmentDirectories().logs or Path("./log")

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
        filter=lambda record: not _console_logging_suppressed,
    )
    loguru.logger.add(
        log_file,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )


@contextmanager
def suppress_console_logging() -> Iterator[None]:
    """
    Suppress the console sink for the duration of the block.

    The file sink keeps logging as normal, so nothing is lost from the log
    file -- this only quiets stderr, for code (e.g. a live-rendered
    progress bar) that a stray log line would visually corrupt. Any logger
    call reached from inside the block is affected, not just ones in the
    caller's own code, since the sink's filter checks a module-level flag
    rather than the call site.
    """
    global _console_logging_suppressed
    _console_logging_suppressed = True
    try:
        yield
    finally:
        _console_logging_suppressed = False


logger = loguru.logger
