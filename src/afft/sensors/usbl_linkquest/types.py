"""Configuration types for LinkQuest TrackLink USBL processing."""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class UsblResolvePositionConfig:
    bearing_reference: str = "absolute"
    timestamp_col: str = "timestamp"
    bearing_col: str = "bearing"
    range_col: str = "range"
    ship_lat_col: str = "latitude"
    ship_lon_col: str = "longitude"
    ship_heading_col: str = "heading"
    depth_col: str = "depth"


@dataclass(slots=True, frozen=True)
class UsblUncertaintyConfig:
    range_uncertainty: float = 15.0
    bearing_uncertainty: float = 20.05
    range_col: str = "range"
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
