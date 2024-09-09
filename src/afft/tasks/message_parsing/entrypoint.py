"""Module for parsing AUV messages via the command-line interface."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from ...runtime import Command
from ...utils.log import logger
from ...utils.result import Ok, Err, Result

from .data_types import MessageParseContext, MessageParseData
from .worker import execute_message_parsing


def parse_arguments(arguments: list[str]) -> Result[Namespace, str]:
    parser = ArgumentParser()

    parser.add_argument("input", type=Path, help="input message file")
    parser.add_argument("output", type=Path, help="output message file")
    parser.add_argument("protocol", type=Path, help="protocol configuration file")

    try:
        namespace: Namespace = parser.parse_args(arguments)
    except ValueError as error:
        return Err(error)

    return Ok(namespace)


def log_task_intro(input: Path, output_file: Path, protocol: Path) -> None:
    """Logs a brief overview of the message parsing task parameters."""

    logger.info("")
    logger.info("Executing message parsing task:")
    logger.info(f" - Input:     {input}")
    logger.info(f" - Output:    {output_file}")
    logger.info(f" - Protocol:  {input}")
    logger.info("")


def configure_task_context(
    input: Path, output: Path, protocol: Path
) -> MessageParseContext:
    """Creates a message parse context based on the"""

    # TODO: Add option to save messages to database

    return MessageParseContext(input, output, protocol)


def configure_task_data(source: Path) -> MessageParseData:
    """TODO"""

    # TODO: Set up message loader
    # TODO: Build protocol
    # TODO: Add export handler

    return MessageParseData(
        message_loader=None,
        protocol_builder=None,
        message_saver=None,
    )


def invoke_message_parsing(command: Command) -> None:
    """Entrypoint for parsing message files."""

    namespace: Namespace = parse_arguments(command.arguments).unwrap()
    log_task_intro(namespace.input, namespace.output, namespace.protocol)

    context: MessageParseContext = configure_task_context(
        namespace.input, namespace.output, namespace.protocol
    )

    data: MessageParseData = configure_task_data(namespace.input)

    execute_message_parsing(context, data)