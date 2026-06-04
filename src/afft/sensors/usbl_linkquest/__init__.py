"""Processing package for the LinkQuest TrackLink 1500HA USBL."""

from afft.sensors.registry import register_sensor

from .parsers import parse_tracklink_log as parse_tracklink_log
from .processors import estimate_usbl_uncertainty as estimate_usbl_uncertainty
from .processors import (
    process_tracklink_usbl_from_logs as process_tracklink_usbl_from_logs,
)
from .processors import (
    process_tracklink_usbl_from_messages as process_tracklink_usbl_from_messages,
)
from .processors import (
    resolve_target_position_from_logs as resolve_target_position_from_logs,
)
from .processors import (
    resolve_target_position_from_messages as resolve_target_position_from_messages,
)
from .types import TrackLinkFixEntry as TrackLinkFixEntry
from .types import TrackLinkRawEntry as TrackLinkRawEntry
from .types import (
    TrackLinkProcessingFromLogsConfig as TrackLinkProcessingFromLogsConfig,
)
from .types import (
    TrackLinkProcessingFromMessagesConfig as TrackLinkProcessingFromMessagesConfig,
)
from .types import (
    TrackLinkResolvePositionFromLogsConfig as TrackLinkResolvePositionFromLogsConfig,
)
from .types import (
    TrackLinkResolvePositionFromMessagesConfig as TrackLinkResolvePositionFromMessagesConfig,
)
from .types import (
    TrackLinkTransceiverExtrinsics as TrackLinkTransceiverExtrinsics,
)
from .types import TrackLinkUncertaintyConfig as TrackLinkUncertaintyConfig

register_sensor(
    "usbl_linkquest",
    TrackLinkProcessingFromMessagesConfig,
    process_tracklink_usbl_from_messages,
)
