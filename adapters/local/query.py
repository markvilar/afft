from functools import partial
from typing import Callable, Dict, List

from icecream import ic

from filetools.io import read_json
from filetools.transfer import Endpoint, TransferAssignment
from filetools.utils import Logger

def create_queries(
    references: Dict,
    source: Endpoint,
    destination: Endpoint,
    logger: Logger=None,
) -> Dict[str, List[TransferAssignment]]:
    """ 
    Creates queries for local groups.

    Args:
     - references:          Reference data for setting up the queries
     - source:              Source endpoint
     - destination:         Destination endpoint
     - target_references:   Target entries in the references

    Return:
     - Dictionary with labelled collections of transfer assignments.
    """

    
    raise NotImplementedError

def build_query_setup_function(
    config: Dict,
    logger: Logger,
) -> Callable[None, Dict[str, List[TransferAssignment]]]:
    """ Creates a function that creates queries based on the configuration. """

    # Read references from file
    references = read_json(config["job"]["entry_file"])

    # Filter references
    if "target_entries" in config["job"]:
        target_entries = [entry.strip() for entry in config["job"]["target_entries"].split(",")]
        filter_by_keys = lambda keys: {x: references[x] for x in keys}
        reference_selection = filter_by_keys(target_entries)
    else:
        reference_selection = references

    ic(type(reference_selection), reference_selection.keys())
    input("Press a key...")

    # Set up source and destination endpoints
    source = Endpoint(
        host=config["source"]["host"], 
        path=config["source"]["root"],
    )
    destination = Endpoint(
        host=config["destination"]["host"], 
        path=config["destination"]["root"],
    )

    query_fun = partial(
        create_queries,
        references = reference_selection,
        source = source,
        destination = destination,
        logger = logger,
    )
