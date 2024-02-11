""" Process image and pose information. """
from pathlib import Path

from loguru import logger
from result import Ok, Err, Result

from auvtools.core.io import read_file
from auvtools.core.utils import create_argument_parser, Namespace

from auvtools.services.renav import read_stereo_pose_file

def validate_arguments(arguments: Namespace) -> Result[Namespace, str]:
    """ Validate the command line arguments. """

    # Validate poses
    if not isinstance(arguments.poses, Path):
        return Err(f"invalid type for argument 'poses'")
    if not arguments.poses.is_file():
        return Err(f"argument 'poses' is not a file: {arguments.poses}")
    if not arguments.poses.suffix == ".data":
        return Err(f"argument 'poses' has invalid suffix: {arguments.poses}")
    
    # Validate selection
    if not isinstance(arguments.includes, Path):
        return Err(f"invalid type for argument 'selection'")
    if not arguments.includes.is_file():
        return Err(f"argument 'selection' is not a file: {arguments.includes}")
    if not arguments.includes.suffix == ".txt":
        return Err(f"argument 'selection' has invalid suffix: {arguments.includes}")

    return Ok(arguments)

def create_stereo_references(pose_file: Path, includes_file: Path):
    """ 
    Create pose reference from a Renav stereo pose file and a selection of 
    labels.
    """
    # Read stereo poses
    result: Result[StereoPoses, str] = read_stereo_pose_file(pose_file)
    if result.is_err():
        logger.error(f"Error when reading file: {pose_file}")
    poses = result.unwrap()

    # Read include labels
    result: Result[List[str], str] = read_file(includes_file)
    if result.is_err():
        logger.error(f"Error when reading includes: {includes_file}")

    includes = result.unwrap()

    logger.info(f"Poses:    {len(poses)}")
    logger.info(f"Includes: {len(includes)}")

    include_poses = list()
    for pose in poses:
        if pose.label in includes:
            include_poses.append(pose)

    logger.info(f"Poses to include: {len(include_poses)}")

    # TODO: Write poses to file

def main():
    """ Entry point. """
    parser = create_argument_parser()
    parser.add_argument("poses",
        type = Path,
        help = "path to pose information file",
    )
    parser.add_argument("includes",
        type = Path,
        help = "path to labels",
    )

    result : Result[Namespace, str] = validate_arguments(parser.parse_args())

    match result:
        case Ok(arguments):
            create_stereo_references(arguments.poses, arguments.includes)
        case Err(message):
            logger.error(message)

if __name__ == "__main__":
    main()
