""" Script for formatting messages from AUV Sirius. """
import argparse

from pathlib import Path

from loguru import logger
from result import Ok, Err, Result

from auvtools.io import read_file
from auvtools.services.sirius import parse_messages

ArgumentParser = argparse.ArgumentParser
Namespace = argparse.Namespace

def process_message_files(arguments: Namespace):
    """ 
    Process a message file line by line with handlers for each message
    identifier. 
    """

    for path in arguments.input:
        read_result : Result[FileLines, str] = read_file(path)
       
        if read_result.is_err():
            logger.error(f"read error: {read_result.unwrap()}")
        
        lines = read_result.unwrap()

        # Prepare strings before parsing
        lines = [ line.expandtabs(4) for line in lines ]

        # Parse strings into messages
        messages = parse_messages(lines)

        # Group messages by identifer
        grouped_messages: Dict[str, List[MessageData] = dict()
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


def validate_arguments(arguments : Namespace) -> Result[Namespace, str]:
    """ Validates command line arguments. """
    for path in arguments.input:
        if not path.is_file():
            return Err(f"path {path} is not a file")
    if not arguments.output.is_dir():
        return Err(f"path {path} is not a directory")
    return Ok(arguments)

def main():
    """ Main function. """
    parser = ArgumentParser()
    parser.add_argument("input", 
        type = Path,
        nargs = "+",
        help = "path to message files",
    )
    parser.add_argument("output", 
        type = Path,
        help = "path to output directory",
    )

    result : Result[Namespace, str] = validate_arguments(
        parser.parse_args()
    )

    match result:
        case Ok(arguments):
            process_message_files(arguments)
        case Err(message):
            print(message)

if __name__ == "__main__":
    main()
