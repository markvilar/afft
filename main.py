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
    create_argument_parser,
    create_logger,
    add_remote_transfer_arguments,
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

    # Read rclone config
    config = rclone.read_config(args.config)
    remotes = rclone.list_remotes(config)

    # Prepare query function (ACFR specific)
    transfer_format_fun = partial(
        create_group_transfers, 
        filepath=args.input, 
        target_labels=args.keys, 
        source_root=Path("/media/water/RAW_DATA"),
        dest_root=Path("/home/martin/data/acfr_dev"),
        logger=logger,
    )
   
    # Prepare transfer job with input stem as label
    transfer_jobs = prepare_transfer(
        source="acfr_archipelago",
        setup_fun=transfer_format_fun,
    )

    # Execute data transfer
    for transfer_job in transfer_jobs:
        execute_transfer(config, transfer_job, logger)

if __name__ == "__main__":
    main()
