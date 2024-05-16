"""Module for time functionality."""

import arrow


def get_time_string(format_string: str = "YYYYMMDD_HHmmss_SSS") -> str:
    """Return the current time as a formatted string."""
    return arrow.get().format(format_string)
