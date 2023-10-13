from filetools.utils import find_files_by_stem
from filetools.utils import create_argument_parser

from filetools.adapters.media import add_directory_cleanup_arguments

def main():
    """ Entry point for directory cleanup. """
    parser = create_argument_parser()
    add_directory_cleanup_arguments(parser)

    parser.parse_args()

if __name__ == "__main__":
    main()
