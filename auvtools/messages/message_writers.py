"""Write functions for message objects."""

from pathlib import Path

import h5py

from result import Ok, Err, Result

from .message_types import MessageData, MessageHeader

Messages = List[MessageData]


def write_messages_to_file(path: Path):
    """Writes messages to"""
    raise NotImplementedError


def write_doppler_to_hdf5(group: object, messages: Messages):
    """TODO"""
