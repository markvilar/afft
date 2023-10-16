from filetools.utils import create_argument_parser, find_files_by_stem

def main():
    """ Entry point for directory cleanup. """
    parser = create_argument_parser()
    parser.parse_args()

if __name__ == "__main__":
    main()
