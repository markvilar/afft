""" Module with logging functionality. """

import logging
import sys

Logger = logging.Logger

def create_logger(name: str="client") -> logging.Logger:
    """ Creates a logger with a file and terminal sink. """
    logger = logging.Logger(name)
    logger.addHandler(logging.FileHandler(name + ".log"))
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger
