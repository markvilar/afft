"""Data types for the collect renav stereo poses task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class CollectRenavStereoPosesCommand:
    """
    Command for collecting and relabelling Renav stereo pose estimate files.

    Attributes
    ----------
    root_dir: Root directory containing deployment subdirectories.
    output_dir: Directory to write the relabelled files into.
    deployment_suffix: Suffix stripped from each deployment subdirectory name
        to derive the deployment label (e.g. ``"_deployment_data"``).
    appendix: Suffix appended to each deployment label to form the output
        filename.
    tiebreak_margin: Fractional row-count margin within which the most recent
        file is preferred over the largest. For example, 0.03 means any file
        within 3% of the maximum row count is a candidate for the tiebreak.
    """

    root_dir: Path
    output_dir: Path
    deployment_suffix: str = "_deployment_data"
    appendix: str = "_renav_stereo_poses.txt"
    tiebreak_margin: float = 0.03
