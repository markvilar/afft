""" Main script for the package where the API is used. """

from functools import partial
from pathlib import Path

import tools.rclone_wrapper as rclone

from tools.adapters.acfr import (
    add_business_arguments,
    create_group_transfers,
)
from tools.transfer import (
    prepare_transfer, 
    execute_transfer,
)
from tools.utils import (
    add_remote_transfer_arguments,
    create_argument_parser,
    create_logger,
    read_config_file,
)

def main():
    """ Executed when the script is invoked. """
    # Create argument parser and logger
    parser = create_argument_parser()
    logger = create_logger()

    # Add relevant arguments to argument parser
    parser = add_remote_transfer_arguments(parser)
    parser = add_business_arguments(parser)

    # Parse arguments
    args = parser.parse_args()

    # Load data config
    config = read_config_file(args.config)

    # Read rclone config
    rclone_config = rclone.read_config(args.rclone)
    remotes = rclone.list_remotes(rclone_config)

    # Prepare query function (ACFR specific)
    transfer_format_fun = partial(
        create_group_transfers, 
        filepath        = Path(config["data"]["file"]), 
        target_labels   = config["data"]["groups"], 
        source_root     = Path(config["remote"]["source_root"]),
        dest_root       = Path(config["paths"]["output"]),
        logger=logger,
    )
   
    # Prepare transfer job with input stem as label
    transfer_jobs = prepare_transfer(
        source=config["remote"]["source"],
        setup_fun=transfer_format_fun,
    )

    # Execute data transfer
    for transfer_job in transfer_jobs:
        execute_transfer(rclone_config, transfer_job, logger)

if __name__ == "__main__":
    main()
