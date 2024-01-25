from typing import Callable, Dict

MessageIdentifiers = [
    "THR_PORT",
    "THR_STBD",
    "THR_VERT",
    "RDI",
    "OAS",
    "PAROSCI",
    "SEABIRD",
    "VIS",
    "ECOPUCK",
]

MessageData = Dict[str, str]
MessageStringFunc = Callable[str, MessageData]

def parse_message_file():
    """ Parse a message file. """
    raise NotImplementedError

def parse_visual_message(message: str) -> MessageData:
    """ Parser function for visual sensor messages. """
    raise NotImplementedError

def parse_pressure_message(message: str) -> MessageData:
    """ Parser function for pressure sensor messages. """
    raise NotImplementedError

def parse_doppler_log_message(message: str) -> MessageData:
    """ Parser function for Doppler log sensor messages. """
    raise NotImplementedError

def parse_thruster_message(message: str) -> MessageData:
    """ Parser function for thruster messages. """
    raise NotImplementedError

def parse_ctd_message(message: str) -> MessageData:
    """ 
    Parser function for conductivity, temperature, pressure sensor 
    messages. 
    """
    raise NotImplementedError

def parser_fls_message(message: str) -> MessageData:
    """ 
    Parser function for forward looking sonar messages (single-beam 
    echosounder). 
    """
    raise NotImplementedError
