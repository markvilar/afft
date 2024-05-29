"""Unit test for rafts logger."""

from raft.utils.log import init_logger


def test_log_initialization() -> None:
    """Test log initialization."""

    init_logger()
