"""Configuration types for LinkQuest TrackLink USBL processing."""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class UsblResolvePositionConfig:
    bearing_reference: str = "absolute"
    timestamp_col: str = "timestamp"
    bearing_col: str = "target_bearing"
    range_col: str = "target_slant_range"
    ship_lat_col: str = "ship_latitude"
    ship_lon_col: str = "ship_longitude"
    ship_heading_col: str = "ship_heading"
    depth_col: str = "depth"
    max_time_gap_seconds: float = 60.0


@dataclass(slots=True, frozen=True)
class UsblUncertaintyConfig:
    range_uncertainty: float = 15.0
    bearing_uncertainty: float = 20.05
    range_col: str = "target_slant_range"
    horizontal_range_col: str = "horizontal_range"
    min_horizontal_range: float = 0.1


@dataclass(slots=True, frozen=True)
class UsblProcessingConfig:
    """
    Combined configuration for the full TrackLink USBL processing pipeline.

    Attributes
    ----------
    resolve: Configuration for position resolution.
    uncertainty: Configuration for uncertainty estimation.
    """

    resolve: UsblResolvePositionConfig = field(
        default_factory=UsblResolvePositionConfig
    )
    uncertainty: UsblUncertaintyConfig = field(
        default_factory=UsblUncertaintyConfig
    )
