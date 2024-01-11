import sys
sys.path.append("../filetools")

from pathlib import Path
from typing import Dict

from icecream import ic

import filetools.transfer.rclone as rclone

from filetools.io import read_json

from filetools.transfer import (
    Endpoint,
    FileQuery,
    DirectoryQuery,
    TransferAssignment,
    TransferJob,
    prepare_transfer, 
    execute_transfer, 
)

from filetools.utils import (
    ArgumentParser,
    Namespace,
    Logger,
    create_argument_parser, 
    create_logger,
    read_config_file,
)

from adapters.archipelago import build_query_setup_function, create_queries

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
    assert arguments.rclone.exists(), \
        f"{arguments.rclone} does not exist"
    assert arguments.rclone.is_file(), \
        f"{arguments.rclone} is not a file"
    
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
    parser.add_argument("--targets",
        type=Path,
        required=True,
        help="transfer target configuration",
    )
    parser.add_argument("--references",
        type=Path,
        required=True,
        help="file references",
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

    targets = read_config_file(arguments.targets)

    logger.info("\nTargets: ")
    for key in targets:
        logger.info(f" - {key}")
   
    # Read the references from file
    references : Dict[str] = read_json(arguments.references)

    logger.info("\nReferences: ")
    for key in references:
        logger.info(f" - {key}")

    # Set up rclone context
    context = rclone.Context(rclone.read_config(arguments.rclone))
    remotes = rclone.list_remotes(context)
    
    logger.info(f"\nTransfer context:")
    logger.info(f" - Config file:   {arguments.rclone}")
    logger.info(f" - Remotes:       {remotes}")

    # Set up source and destination endpoints
    source = Endpoint(
        host = config["endpoints"]["source"]["host"], 
        path = config["endpoints"]["source"]["directory"],
    )
    destination = Endpoint(
        host=config["endpoints"]["destination"]["host"], 
        path=config["endpoints"]["destination"]["directory"],
    )

    # TODO: Filter based on groups
    logger.info("\nReferences:")
    assignments = dict()
    for group in references:
        for deployment in references[group]:

            logger.info(f" - {group} / {deployment}")

            queries = {
                "directories" : list(),
                "files" : list(),
            }
            
            # TODO: Use source and destination paths to set up queries 
            # per deployment within each group
            items = references[group][deployment]["items"]
           
            # For each entry - create directory / files query
            for key in targets:
               
                target = {
                    "type" : targets[key]["type"],
                    "reference" : targets[key]["reference"],
                    "destination" : targets[key]["destination"],
                }

                # TODO: Set up destination directory
                directory = destination.path / Path(group) / Path(deployment)
   
                # If target are files
                match target["type"]:
                    case "files":
                        reference = target["reference"]
                        files = items["files"][reference]

                        logger.info(f" - {key} : \t\t {len(files)}")
                        
                        query = FileQuery(
                            source = source.path,
                            destination = destination.path / Path(target["destination"]),
                            include_files = files,
                        )
                        queries["files"].append(query)

                    case "directory":
                        reference = target["reference"]
                        directory = items["directories"][reference]

                        logger.info(f" - {key} : \t\t {directory}")
                        
                        query = DirectoryQuery(
                            source = source.path / Path(directory),
                            destination = destination.path / Path(target["destination"]),
                        )

                        queries["directories"].append(query)

            
            assignments[deployment] = TransferAssignment(
                directory_queries = queries["directories"],
                file_queries = queries["files"],
            )
           
        transfer_jobs = list()
        for deployment in assignments:
            transfer_jobs.append(
                TransferJob(
                    label = deployment,
                    source = source,
                    destination = destination,
                    assignment = assignments[deployment],
                )
            )
            
        for job in transfer_jobs:
            execute_transfer(context, job, logger)

if __name__ == "__main__":
    main()
