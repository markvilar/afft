""" Main script for the package where the API is used. """

from functools import partial
from pathlib import Path

import filetools.transfer.rclone as rclone

from filetools.transfer import (
    prepare_transfer, 
    execute_transfer,
)
from filetools.utils import (
    create_argument_parser,
    create_logger,
    read_config_file,
)

from adapters.archipelago import create_group_queries

def main():
    """ Executed when the script is invoked. """
    # Create argument parser and logger
    parser = create_argument_parser()
    logger = create_logger()

    # Add relevant arguments to argument parser
    parser.add_argument("destination",
        type = Path,
        help = "destination folder for the transfer",
    )
    parser.add_argument("--rclone",
        type=Path,
        required=False,
        default=Path.home() / Path(".config/rclone/rclone.conf"),
        help="rclone config file path",
    )
    parser.add_argument("--config",
        type=Path,
        required=True,
        help="config file path",
    )

    # Parse arguments
    arguments = parser.parse_args()

    # Load data config
    config = read_config_file(arguments.config)

    # Read rclone config
    rclone_config = rclone.read_config(arguments.rclone)
    remotes = rclone.list_remotes(rclone_config)

    logger.info(f"Rclone:")
    logger.info(f" - Config file:   {arguments.rclone}")
    logger.info(f" - Remotes:       {remotes}")

    # Prepare assignment setup function
    setup_fun = partial(
        create_group_queries, 
        source_root     = Path(config["source"]["root"]),
        dest_root       = Path(config["destination"]["root"]),
        filepath        = Path(config["job"]["entry_file"]), 
        target_groups   = config["job"]["target_entries"],
        logger=logger,
    )
   
    # Prepare transfer job with input stem as label
    transfer_jobs = prepare_transfer(
        source = config["source"]["label"],
        assignment_setup_fun = setup_fun,
    )

    # Execute data transfer
    for transfer_job in transfer_jobs:
        execute_transfer(rclone_config, transfer_job, logger)

if __name__ == "__main__":
    main()
