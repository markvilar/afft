""" Functionality to export messages to file. """

from ..services.sirius import MessageHeader, MessageData

def export_messages(messages: List[MessageData]):
    """ Process a message file line by line with handlers for each message
    identifier. """

    # Group messages by identifer
    grouped_messages = dict()
    for message in messages:
        if not message.header.identifier in grouped_messages:
            grouped_messages[message.header.identifier] = list()
        grouped_messages[message.header.identifier].append(message)

    # Message group statistics
    logger.info(f"\nMessage statistics:")
    for identifier in grouped_messages:
        count = len(grouped_messages[identifier])
        logger.info(f" - {identifier} : {count}")

    logger.info(f"\nMessage fields:")
    for identifier in grouped_messages:
        field_keys = list(grouped_messages[identifier][0].payload.keys())
        logger.info(f" - {identifier} : {field_keys}")

