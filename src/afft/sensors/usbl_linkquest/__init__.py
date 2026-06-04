"""Processing package for the LinkQuest TrackLink 1500HA USBL."""

from afft.sensors.registry import register_sensor

from .parsers import parse_tracklink_log as parse_tracklink_log
from .processors import estimate_usbl_uncertainty as estimate_usbl_uncertainty
from .processors import process_tracklink_usbl as process_tracklink_usbl
from .processors import resolve_usbl_position as resolve_usbl_position
from .types import TrackLinkFixEntry as TrackLinkFixEntry
from .types import TrackLinkRawEntry as TrackLinkRawEntry
from .types import TrackLinkProcessingConfig as TrackLinkProcessingConfig
from .types import (
    TrackLinkResolvePositionConfig as TrackLinkResolvePositionConfig,
)
from .types import (
    TrackLinkTransceiverExtrinsics as TrackLinkTransceiverExtrinsics,
)
from .types import TrackLinkUncertaintyConfig as TrackLinkUncertaintyConfig

register_sensor(
    "usbl_linkquest", TrackLinkProcessingConfig, process_tracklink_usbl
)
