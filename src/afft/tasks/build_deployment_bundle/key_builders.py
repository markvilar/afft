"""Plain functions constructing the bundle key each section builder writes
to, with no dependency on the data being written."""


def deployment_identity_key() -> str:
    return "deployment/identity"


def deployment_metadata_key() -> str:
    return "deployment/metadata"


def deployment_files_key() -> str:
    return "deployment/files"


def deployment_provenance_key() -> str:
    return "deployment/provenance"


def root_identity_key(root: str) -> str:
    return f"{root}/identity"


def sensor_identity_key(root: str, sensor_key: str) -> str:
    return f"{root}/sensors/{sensor_key}/identity"


def sensor_message_topics_key(root: str, sensor_key: str) -> str:
    return f"{root}/sensors/{sensor_key}/message_topics"


def sensor_extrinsics_key(root: str, sensor_key: str) -> str:
    return f"{root}/sensors/{sensor_key}/extrinsics"


def sensor_calibration_key(root: str, sensor_key: str) -> str:
    return f"{root}/sensors/{sensor_key}/calibration"


def raw_telemetry_key(sensor_key: str, topic: str) -> str:
    return f"telemetry/raw/{sensor_key}/{topic}/messages"
