from dataclasses import dataclass
from typing import Dict

MessageIDs = [
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

MessageNames = {
    "THR_PORT": "port_thruster",
    "THR_STBD": "starboard_thruster",
    "THR_VERT": "vertical_thruster",
    "RDI": "doppler_log",
    "OAS": "echosounder",
    "PAROSCI": "pressure",
    "SEABIRD": "seabird",
    "VIS": "visual",
    "ECOPUCK": "ecopuck",
}

# Validate message parsers
for identifier in MessageIDs:
    assert (
        identifier in MessageNames
    ), f"found no name for message identifier {identifier}"


@dataclass
class MessageHeader:
    identifier: str
    timestamp: float


@dataclass
class MessageData:
    header: MessageHeader
    payload: Dict[str, str | int | float]
