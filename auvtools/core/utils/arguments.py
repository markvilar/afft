""" Module for reading and parsing command line arguments. """

import argparse

ArgumentParser = argparse.ArgumentParser
Namespace = argparse.Namespace

def create_argument_parser() -> ArgumentParser:
    """ Creates an argument parser. """
    return ArgumentParser()
