"""Data types for the SEABED vehicle system config (``*.SEABED.syscfg``)."""

from pydantic import BaseModel, ConfigDict


class VehicleInfo(BaseModel):
    """
    Vehicle identity from the ``syscfg`` block.

    Attributes
    ----------
    vehicle_name: Vehicle name (e.g. ``"SEABED"``).
    vehicle_config: Vehicle configuration (e.g. ``"NORM_CFG"``).
    """

    model_config = ConfigDict(frozen=True)

    vehicle_name: str
    vehicle_config: str


class SensorEntry(BaseModel):
    """
    A single sensor from the ``sensors`` block roster.

    Attributes
    ----------
    name: Sensor label (e.g. ``"RDI"``).
    driver: Sensor driver (e.g. ``"SIO_rdi"``).
    transport: Port type (``"SERIAL"`` | ``"NETWORK_TCPIP"`` | ``"NETWORK_UDP"``).
    """

    model_config = ConfigDict(frozen=True)

    name: str
    driver: str
    transport: str


class SensorConfig(BaseModel):
    """
    The ``sensors`` block: the roster of configured sensors.

    Attributes
    ----------
    entries: Configured sensors, one per active roster row.
    """

    model_config = ConfigDict(frozen=True)

    entries: list[SensorEntry]


class LoggerConfig(BaseModel):
    """
    Logging configuration from the ``logger`` block.

    Attributes
    ----------
    log_dir: On-vehicle log directory (e.g. ``"/files1/Log"``).
    logged_streams: Stream types written to disk, from ``log_to_disk``
        (e.g. ``["SYSLOG", "RAW", "CTL", "AUV", "MSG", "RDI"]``).
    """

    model_config = ConfigDict(frozen=True)

    log_dir: str
    logged_streams: list[str]


class SeabedSystemConfig(BaseModel):
    """
    The common blocks of a SEABED vehicle system config (``*.SEABED.syscfg``).

    Attributes
    ----------
    vehicle: Vehicle identity (``syscfg`` block).
    sensors: Configured sensor roster (``sensors`` block).
    logger: Logging configuration (``logger`` block).
    """

    model_config = ConfigDict(frozen=True)

    vehicle: VehicleInfo
    sensors: SensorConfig
    logger: LoggerConfig
