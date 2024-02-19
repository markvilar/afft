from dataclasses import dataclass
from pathlib import Path

from result import Ok, Err, Result

@dataclass
class Endpoint():
    host: str
    path: Path

    def as_string(self) -> str:
        """ Return the string representation of the endpoint. """
        return self.host + ":" + str(self.path)

def create_endpoint_from_string(
    string : str
) -> Result[Endpoint, BaseException]:
    """ 
    Create an endpoint from a string consisting of hostname and path on the
    format <hostname>:<path>. 
    """
    splits = string.split(":")
    if not len(splits) == 2:
        return Err(f"invalid endpoint string: {string}")
    
    endpoint = Endpoint(host=splits[0], path=splits[1])
    return Ok(endpoint) 

