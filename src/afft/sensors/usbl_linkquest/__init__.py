"""LinkQuest TrackLink USBL sensor processing."""

from afft.sensors.registry import register_sensor

from .processors import estimate_usbl_uncertainty as estimate_usbl_uncertainty
from .processors import process_tracklink_usbl as process_tracklink_usbl
from .processors import resolve_usbl_position as resolve_usbl_position
from .types import UsblProcessingConfig as UsblProcessingConfig
from .types import UsblResolvePositionConfig as UsblResolvePositionConfig
from .types import UsblTransceiverExtrinsics as UsblTransceiverExtrinsics
from .types import UsblUncertaintyConfig as UsblUncertaintyConfig

register_sensor("usbl_linkquest", UsblProcessingConfig, process_tracklink_usbl)
