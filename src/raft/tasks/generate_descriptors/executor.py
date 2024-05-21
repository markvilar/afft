"""Module for executing group descriptor generation."""

from pathlib import Path
from typing import Callable

from result import Ok, Err, Result

from raft.filesystem import list_directory, search_directory
from raft.io import write_toml
from raft.utils.log import logger

from .data_types import DeploymentIndex, DeploymentIndexGroup


def check_directory(path: Path, checker: Callable[[Path], bool]) -> Result[Path, str]:
    """Performs a check on the given directory."""
    if not checker(path):
        return Err(f"check failed for path: {path}")
    else:
        return Ok(path)


def reference_and_validate_subdirectories(
    parent: Path,
    directory_structure: dict[str, str],
    validator: Callable[[Path], bool],
) -> dict[str, Path]:
    """Creates and validates subdirectory paths with a parent directory.

    Arguments:
     - parent: parent directory path
     - directory_structure: subdirectory names with associated keys
    """

    # Create map from key to absoluate subdirectory path
    subdirectories: dict[str, Path] = {
        name: parent / subdirectory
        for name, subdirectory in directory_structure.items()
    }

    validate_subdirectories: dict[str, Path] = dict()
    for key, subdirectory in subdirectories.items():
        is_valid: bool = validator(subdirectory)

        if not is_valid:
            logger.error(f"invalid subdirectory: {subdirectory}")
        else:
            validate_subdirectories[key]: Path = subdirectory

    return validate_subdirectories


def create_deployment_index(
    name: str, subdirectories: dict[str, Path]
) -> DeploymentIndex:
    """Creates a deployment index."""

    search_result: Result[list[Path], str] = search_directory(
        subdirectories["messages"], pattern="*.RAW.auv", recursive=False
    )

    if search_result.is_err():
        logger.error(search_result.err())

    message_files: list[Path] = search_result.ok()

    search_result: Result[list[Path], str] = search_directory(
        subdirectories["cameras"], pattern="*/stereo_pose_est.data", recursive=True
    )

    if search_result.is_err():
        logger.error(search_result.err())

    camera_files: list[Path] = search_result.ok()

    return DeploymentIndex(name=name, messages=message_files, cameras=camera_files)


def export_group_descriptor(group: DeploymentIndexGroup, output_file: Path) -> None:
    """Export a group descriptor to file."""

    deployment_data: list[dict] = list()
    for deployment in group.deployments:

        messages: list[str] = sorted(
            [str(file.relative_to(group.directory)) for file in deployment.messages]
        )
        cameras: list[str] = sorted(
            [str(file.relative_to(group.directory)) for file in deployment.cameras]
        )

        deployment_data.append(
            {"name": deployment.name, "messages": messages, "cameras": cameras}
        )

    group_data = {"deployment": deployment_data}

    write_result: Result[Path, str] = write_toml(group_data, output_file)

    if write_result.is_err():
        logger.error(write_result.err())
    else:
        logger.info(f"wrote group descriptor: {output_file}")


def generate_group_descriptors(root: Path, output: Path, prefix: str) -> None:
    """Generate descriptors for a group of deployments. The procedure searches for message
    and camera files for each deployment."""

    # Add directories in root directory as deployment candidates
    deployments: list[Path] = sorted(
        [path for path in list_directory(root) if path.is_dir()]
    )

    # NOTE: Consider moving to a config file
    # Set up map from name to subdirectory name
    subdirectory_structure: dict[str, str] = {
        "cameras": "camera_poses",
        "messages": "messages",
    }

    # Reference subdirectories for each parent based the given structure
    directory_tree: dict[str, Path] = dict()
    for deployment in deployments:
        subdirectories: dict[str, Path] = reference_and_validate_subdirectories(
            deployment,
            subdirectory_structure,
            validator=lambda path: path.exists() and path.is_dir(),
        )

        directory_tree[deployment] = subdirectories

    # For each deployment - create an index
    deployment_indices: list[DeploymentIndex] = list()
    for parent, subdirectories in directory_tree.items():
        deployment_index: DeploymentIndex = create_deployment_index(
            parent.name, subdirectories
        )
        deployment_indices.append(deployment_index)

    group: DeploymentIndexGroup = DeploymentIndexGroup(
        name=root.name, directory=root, deployments=deployment_indices
    )

    export_group_descriptor(group, output / f"{group.name}_group_descriptor.toml")
