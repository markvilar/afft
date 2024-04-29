"""Package for processing of AUV messages."""

from .config import MessagePaths, MessageProtocol
from .line_readers import read_message_lines
from .task_manager import process_messages
