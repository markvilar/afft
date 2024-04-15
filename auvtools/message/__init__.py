"""Package for processing of AUV messages."""

from .config import MessagePaths, MessageProtocol
from .message_readers import read_message_lines
from .task_manager import process_messages
