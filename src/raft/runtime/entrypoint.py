"""Module for task entrypoint interfaces."""

import functools

from dataclasses import dataclass
from typing import Callable

from raft.utils.log import logger

type ParseResult = Result[Namespace, str]
type Parser = Callable[[list[str]], ParseResult]


def cli_entrypoint(parse_fun, task_fun) -> None:
    """TODO"""

    @functools.wraps(task_fun)
    def wrapper(*args, **kwargs) -> None:

        logger.info(task_fun)


        parse_result: Result[Namespace, str] = parse_fun(arguments)
        if parse_result.is_err():
            logger.error(parse_result.err())

        logger.info(parse_result.ok())

        # Invoke task function with the given namespace
        task_fun(namespace)

    return wrapper
