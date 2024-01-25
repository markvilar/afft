""" Tool to transfer files from ACFR. """

# FIXME: Find a more sustainable long-term solution than to append relative
# directories to the system path
import sys
sys.path.append("../filetools")

from pathlib import Path
from typing import Dict, List

from tqdm import tqdm
from icecream import ic

import filetools.transfer.rclone as rclone

from filetools.io import read_json

from filetools.transfer import (
    Endpoint,
    FileSearch,
    FileQueryData,
    query_files,
)

from filetools.utils import (
    ArgumentParser,
    Namespace,
    Logger,
    create_argument_parser, 
    create_logger,
    read_config_file,
)

# NOTE: Source / file structure dependent
def filter_valid_searches(
    searches: Dict[str, Dict],
    routes: Dict[str, Dict],
    logger: Logger,
) -> List[FileSearch]:
    """ 
    Set up valid searches based on a collection of routes and a search lookup.

    Args:
     - searches:    mapping from key to directory and include files
     - routes:      mapping from search to destination directory
    """

    # Filter routes with search in the search lookup
    valid_routes = list()
    for label in routes:
        search = routes[label]["search"]
        if search in searches:
            valid_routes.append(label)
        else:
            logger.warning(f" - Route {key}: Could not find search {search}")
    
    valid_searches : List[FileSearch] = list()
    for label in valid_routes:
        # The directory and files we are searching for
        search = routes[label]["search"] 
        
        # The destination of the files found in the search
        destination = routes[label]["destination"]
     
        # The directory and include keywords to look for at the source
        directory = searches[search]["directory"]
        searches[search]["include"]

        # TODO: Add capability to exclude files in the future
        file_search = FileSearch(
            source = searches[search]["directory"],
            destination = routes[label]["destination"],
            includes = searches[search]["include"],
        )
        valid_searches.append(file_search)
    
    return valid_searches
        
    """
    # For each entry - create directory / files query
    for key in targets:
       
        target = {
            "reference" : targets[key]["reference"],
            "destination" : targets[key]["destination"],
        }

        logger.info(f"\t - Target: {key}")

        destination_directory = destination.path / Path(group) \
            / Path(deployment) / Path(target["destination"])

        # If target are files
        match target["type"]:
            case "files":
                reference = target["reference"]
                query = FileQuery(
                    source = source.path,
                    destination = destination_directory,
                    include_files = items["files"][reference],
                )
                queries["files"].append(query)

            case "directory":
                reference = target["reference"]
                query = DirectoryQuery(
                    source = source.path / Path(items["directories"][reference]),
                    destination = destination_directory,
                )
                queries["directories"].append(query)
    
    return TransferAssignment(
        directory_queries = queries["directories"],
        file_queries = queries["files"],
    )
    """

def split_endpoint_string(endpoint_string: str) -> Dict[str, str]:
    """ 
    Return the host and directory components of an endpoint as a 
    dictionary. 
    """
    splits = endpoint_string.split(":")
    assert len(splits) == 2, f"invalid endpoint string {endpoint_string}"
    
    endpoint = dict()
    endpoint["host"] = splits[0]
    endpoint["directory"] = splits[1]
    return endpoint

def validate_arguments(arguments: Namespace, logger) -> Namespace:
    """ Validate the command line arguments for the cleanup action. """
    files = [ arguments.rclone, arguments.routes, arguments.searches ]
    for path in files:
        assert path.exists(), f"{path} does not exist"
        assert path.is_file(), f"{path} is not a file"
    return arguments

def main():
    """ Entry point for directory cleanup. """
    parser = create_argument_parser()
    logger = create_logger()

    # Add cleanup job arguments to argument parser
    parser.add_argument("--rclone",
        type=Path,
        required=False,
        default=Path.home() / Path(".config/rclone/rclone.conf"),
        help="rclone config file path",
    )
    parser.add_argument("--source",
        type=str,
        required=True,
        help="transfer source, i.e. <host>:<directory>",
    )
    parser.add_argument("--destination",
        type=str,
        required=True,
        help="transfer destination, i.e. <host>:<directory>",
    )
    parser.add_argument("--routes",
        type=Path,
        required=True,
        help="routing configuration file",
    )
    parser.add_argument("--searches",
        type=Path,
        required=True,
        help="file search configuration file",
    )
    parser.add_argument("--dry-run",
        action="store_true", 
        help="execute a dry action"
    ) 

    # Parse and validate the relevant arguments
    arguments = validate_arguments(parser.parse_args(), logger)
   
    # Set up endpoints
    config = dict()
    config["endpoints"] = dict()
    config["endpoints"]["source"] = split_endpoint_string(arguments.source)
    config["endpoints"]["destination"] = split_endpoint_string(arguments.destination)

    logger.info("\nEndpoints: ")
    for key in config["endpoints"]:
        logger.info(f" - {key}")

    config["routes"] = read_config_file(arguments.routes)

    logger.info("\nRoutes: ")
    for route in config["routes"]:
        logger.info(f" - {route}")
   
    # Read the queries from file
    config["searches"] = read_json(arguments.searches)

    logger.info("\nSearches: ")
    for search in config["searches"]:
        logger.info(f" - {search}")

    # Set up rclone context
    context = rclone.Context(rclone.read_config(arguments.rclone))
    remotes = rclone.list_remotes(context)
    
    logger.info(f"\nTransfer context:")
    logger.info(f" - Config file:   {arguments.rclone}")
    logger.info(f" - Remotes:       {remotes}")

    # Set up queries for each search - NOTE: Source and file dependent
    jobs = dict()
    for label in config["searches"]:
        # Filter searches based on routes
        valid_searches : List[FileSearch] = filter_valid_searches(
            config["searches"][label]["queries"],
            config["routes"],
            logger,
        )

        # Create source endpoint root
        source = Endpoint(
            host = config["endpoints"]["source"]["host"], 
            path = Path(config["endpoints"]["source"]["directory"]),
        )

        # Create local endpoint root - label = group/deployment
        destination = Endpoint(
            host = config["endpoints"]["destination"]["host"], 
            path = Path(config["endpoints"]["destination"]["directory"]) / label ,
        )

        # Set up transfer for each search
        query_data = list()
        for search in valid_searches:
            source = Endpoint(
                host = config["endpoints"]["source"]["host"], 
                path = Path(config["endpoints"]["source"]["directory"]) / search.source,
            )
            destination = Endpoint(
                host = config["endpoints"]["destination"]["host"], 
                path = Path(config["endpoints"]["destination"]["directory"]) \
                    / label / search.destination,
            )

            file_query = FileQueryData(
                source = source,
                destination = destination,
                includes = search.includes,
                excludes = search.excludes,
            )
            
            query_data.append(file_query)

        jobs[label] = query_data
   
    # Query files
    for label in jobs:
        for query_data in tqdm(jobs[label], desc = "\nQuerying files..."):
            result = query_files(
                context = context,
                data = query_data,
                logger = logger,
            )

if __name__ == "__main__":
    main()
