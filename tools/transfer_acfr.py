import sys
sys.path.append("../filetools")

from pathlib import Path

from icecream import ic

import filetools.transfer.rclone as rclone

from filetools.io import read_json
from filetools.transfer import prepare_transfer, execute_transfer, Endpoint
from filetools.utils import (
    ArgumentParser,
    Namespace,
    Logger,
    create_argument_parser, 
    create_logger,
    read_config_file,
)

# from adapters.local import build_query_setup_function

def validate_arguments(arguments: Namespace, logger) -> Namespace:
    """ Validate the command line arguments for the cleanup action. """
    assert arguments.rclone.exists(), \
        f"{arguments.rclone} does not exist"
    assert arguments.rclone.is_file(), \
        f"{arguments.rclone} is not a file"
    assert arguments.endpoints.exists(), \
        f"{arguments.endpoints} does not exist"
    assert arguments.endpoints.is_file(), \
        f"{arguments.endpoints} is not a file"
    assert arguments.targets.exists(), \
        f"{arguments.targets} does not exist"
    assert arguments.targets.is_file(), \
        f"{arguments.targets} is not a file"
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
    parser.add_argument("--endpoints",
        type=Path,
        required=True,
        help="endpoint file path",
    )
    parser.add_argument("--targets",
        type=Path,
        required=True,
        help="target file path",
    )
    parser.add_argument("--dry-run",
        action="store_true", 
        help="execute a dry action"
    ) 

    # Parse and validate the relevant arguments
    arguments = validate_arguments(parser.parse_args(), logger)
   
    config = dict()
    config["endpoint"] = read_config_file(arguments.endpoints)
    config["targets"] = read_config_file(arguments.targets)

    # Set up rclone context
    context = rclone.Context(rclone.read_config(arguments.rclone))
    remotes = rclone.list_remotes(context)
    logger.info(f"Transfer context:")
    logger.info(f" - Config file:   {arguments.rclone}")
    logger.info(f" - Remotes:       {remotes}")

    # Set up source and destination endpoints
    source = Endpoint(
        host=config["endpoint"]["source"]["host"], 
        path=config["endpoint"]["source"]["root"],
    )
    destination = Endpoint(
        host=config["endpoint"]["destination"]["host"], 
        path=config["endpoint"]["destination"]["root"],
    )

    result = rclone.list_directories(context, destination.host, destination.path)
    ic(result)

    # TODO: Make the query not dependent on the source and destination
    # Set up query setup function for local transfers
    # query_fun = build_query_setup_function(source, destination, config, logger)
  
    # Prepare to execute transfers
    jobs = prepare_transfer(
        source = source,
        destination = destination,
        assignment_setup_fun = query_fun
    )
    
    # Execute transfers
    for job in jobs:
        execute_transfer(
            context = context,
            job = job,
            logger = logger,
        )

if __name__ == "__main__":
    main()
