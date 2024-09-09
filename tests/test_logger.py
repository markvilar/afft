"""Unit test for the afft logger."""

from afft.utils.log import init_logger


def test_log_initialization() -> None:
    """Test log initialization."""

    init_logger()
