""" Functionality to export messages to file. """
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from loguru import logger

from ..services.sirius import MessageHeader, MessageData

Messages = List[MessageData]
MessageExporter = Callable[[Path, Messages], None]

@dataclass 
class MessageExportData():
    """ Data class for message export. """
    messages: Messages
    output_path: Path
    exporters: Dict[str, MessageExporter]=None

def group_messages_by_identifier(messages: Messages) -> Dict[str, Messages]:
    """ Groups messages by their identifier. """
    message_groups = dict()
    for message in messages:
        if not message.header.identifier in message_groups:
            message_groups[message.header.identifier] = list()
        message_groups[message.header.identifier].append(message)
    return message_groups

def export_messages(export_data: MessageExportData):
    """ Process a message file line by line with handlers for each message
    identifier. """

    # Group messages by identifer
    message_groups = group_messages_by_identifier(export_data.messages)

    # Message group statistics
    logger.info(f"\nMessage statistics:")
    for identifier in message_groups:
        count = len(message_groups[identifier])
        logger.info(f" - {identifier} : {count}")

    logger.info(f"\nMessage fields:")
    for identifier in message_groups:
        field_keys = list(message_groups[identifier][0].payload.keys())
        logger.info(f" - {identifier} : {field_keys}")

    # TODO: Dispatch to exporters based on identifier
    for identifier in message_groups:
        logger.info(f"Identifier: {identifier}")
