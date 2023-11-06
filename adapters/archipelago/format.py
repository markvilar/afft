from pathlib import Path
from typing import List

def replace_file_extensions(
    filepaths: List[Path], 
    extensions: List[str],
) -> List[Path]:
    """ File formatting function that replaces the extension with the given
    extensions. """
    updated_filepaths = list()
    for filepath in filepaths:
        updated_filepaths += [ 
            Path(filepath).with_suffix(extension) for extension in extensions
        ]
    return updated_filepaths

def append_wildcard_to_prefix(
    filepaths: List[Path], 
    prefix_length: int,
    wildcard: str,
) -> List[Path]:
    """ File formatting function that extracts the common part of images and
    appends a completion wildcard. """
    # Sanity check
    for filepath in filepaths:
        assert len(filepath) >= prefix_length, \
            f"{filepath} is not longer than prefix length {prefix_length}"

    # Get prefixes and append wildcard
    updated_filepaths = list()
    for filepath in filepaths:
        updated_filepaths.append(filepath[:prefix_length] + wildcard)
    return updated_filepaths

