"""Data types for the SEABED localizer config (``*.SEABED.localiser.cfg``)."""

from pydantic import BaseModel, ConfigDict


class Origin(BaseModel):
    """
    Geodetic origin of the deployment.

    Attributes
    ----------
    latitude: Latitude in decimal degrees.
    longitude: Longitude in decimal degrees.
    """

    model_config = ConfigDict(frozen=True)

    latitude: float
    longitude: float


class SensorPoseEntry(BaseModel):
    """
    A named sensor extrinsic pose, parsed from a ``<NAME>_POSE_*`` family.

    Frame: SNAME body frame (x forward, y starboard, z down). Translation in
    metres; rotation in radians as ZYX intrinsic Euler (yaw ``rotz``, pitch
    ``roty``, roll ``rotx``).

    Attributes
    ----------
    label: Sensor identifier — the lowercased ``<NAME>`` prefix of the pose
        family (e.g. ``"dvl"``, ``"usbl_transceiver"``, ``"nav_frame"``).
    locx, locy, locz: Translation in metres (from ``_X`` / ``_Y`` / ``_Z``).
    rotx, roty, rotz: Roll / pitch / yaw in radians (from ``_PHI`` / ``_THETA``
        / ``_PSI``).
    """

    model_config = ConfigDict(frozen=True)

    label: str
    locx: float
    locy: float
    locz: float
    rotx: float
    roty: float
    rotz: float


class AuvSensorConfig(BaseModel):
    """
    AUV sensor extrinsics, in the vehicle (SNAME) body frame.

    Attributes
    ----------
    sensor_poses: One entry per pose family in the AUV section.
    """

    model_config = ConfigDict(frozen=True)

    sensor_poses: list[SensorPoseEntry]


class ShipSensorConfig(BaseModel):
    """
    Ship sensor extrinsics, in the ship frame.

    Attributes
    ----------
    sensor_poses: One entry per pose family in the ship section.
    """

    model_config = ConfigDict(frozen=True)

    sensor_poses: list[SensorPoseEntry]


class SeabedLocalizerConfig(BaseModel):
    """
    The description-relevant entries of a SEABED localizer config.

    Attributes
    ----------
    origin: Geodetic origin (``LATITUDE`` / ``LONGITUDE``).
    auv_sensors: AUV sensor extrinsics (``# AUV Sensor Configuration``
        section).
    ship_sensors: Ship sensor extrinsics (``# Ship Sensor Configuration``
        section).
    """

    model_config = ConfigDict(frozen=True)

    origin: Origin
    auv_sensors: AuvSensorConfig
    ship_sensors: ShipSensorConfig
