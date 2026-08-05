"""Round-trip tests for the pandas.HDFStore deployment bundle implementation."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from afft.deployment.bundle_hdf_readers import open_deployment_bundle_reader
from afft.deployment.bundle_hdf_writers import open_deployment_bundle_writer
from afft.deployment.bundle_types import (
    DeploymentBundleHeader,
    DeploymentIdentity,
    DeploymentProvenance,
    ProcessedProvenance,
)
from afft.deployment.common_types import (
    DeploymentMetadata,
    PlatformIdentity,
    PlatformSensor,
    SensorCalibration,
    SensorExtrinsics,
    SensorIdentity,
    VesselIdentity,
    VesselSensor,
)


def _header() -> DeploymentBundleHeader:
    return DeploymentBundleHeader(
        schema_version="1.0",
        created_datetime=datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc),
        builder_version="0.1.0",
    )


def test_write_header_and_deployment_section(tmp_path: Path) -> None:
    """Round-trips the bundle header and the deployment section's records."""
    path = tmp_path / "bundle.h5"
    identity = DeploymentIdentity(
        deployment_label="qc2hyd_20231021T032349Z",
        deployment_datetime=datetime(
            2023, 10, 21, 3, 23, 49, tzinfo=timezone.utc
        ),
    )
    metadata = DeploymentMetadata(
        acfr_deployment_label="r20231021_032349_qc2hyd",
        acfr_campaign_label="r20231021_qc2hyd",
        acfr_platform_label="sirius",
        origin_latitude=-33.5,
        origin_longitude=151.3,
        magnetic_variation=12.4,
    )
    provenance = DeploymentProvenance(deployment_key="qc2hyd_20231021T032349Z")
    files = pd.DataFrame(
        {"role": ["stereo_pose"], "path": ["stereo_pose_est.data"]}
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.deployment.write_identity(identity)
        writer.deployment.write_metadata(metadata)
        writer.deployment.write_provenance(provenance)
        writer.deployment.write_files(files)

    with open_deployment_bundle_reader(path) as reader:
        assert reader.header == _header()
        assert reader.deployment.identity() == identity
        assert reader.deployment.metadata() == metadata
        assert reader.deployment.provenance() == provenance
        assert reader.deployment.files()["role"].tolist() == ["stereo_pose"]


def test_write_once_raises_on_second_write(tmp_path: Path) -> None:
    """A write-once method raises if the target node already exists."""
    path = tmp_path / "bundle.h5"
    identity = DeploymentIdentity(
        deployment_label="qc2hyd_20231021T032349Z",
        deployment_datetime=datetime(
            2023, 10, 21, 3, 23, 49, tzinfo=timezone.utc
        ),
    )
    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.deployment.write_identity(identity)
        with pytest.raises(ValueError):
            writer.deployment.write_identity(identity)


def test_platform_sensor_roster_round_trip(tmp_path: Path) -> None:
    """
    Round-trips a platform sensor roster, including a sensor with no
    extrinsics/calibration and one with an empty message_topics list.
    """
    path = tmp_path / "bundle.h5"
    dvl = PlatformSensor(
        key="dvl_teledyne_navigator",
        message_topics=["RDI"],
        identity=SensorIdentity(
            label="DVL", vendor="Teledyne RDI", product="Navigator", type="dvl"
        ),
        extrinsics=SensorExtrinsics(
            locx=0.1, locy=0.0, locz=0.2, rotx=0.0, roty=0.0, rotz=0.0
        ),
        calibration=None,
    )
    camera = PlatformSensor(
        key="vis_camera",
        message_topics=[],
        identity=SensorIdentity(
            label="VIS camera", vendor="", product="", type="camera"
        ),
        extrinsics=None,
        calibration=SensorCalibration(
            calibration_type="pinhole",
            parameters={"fx": 1043.2, "fy": 1043.2, "cx": 512.0, "cy": 384.0},
        ),
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.platform.write_identity(
            PlatformIdentity(
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="ACFR",
            )
        )
        writer.platform.write_sensors([dvl, camera])

    with open_deployment_bundle_reader(path) as reader:
        assert reader.platform.sensor_keys() == [
            "dvl_teledyne_navigator",
            "vis_camera",
        ]
        sensors = {sensor.key: sensor for sensor in reader.platform.sensors()}

        assert sensors["dvl_teledyne_navigator"] == dvl
        assert sensors["vis_camera"] == camera
        # message_topics=[] is not written as a node; reads back as [].
        assert not reader.contains("platform/sensors/vis_camera/message_topics")
        # extrinsics=None is not written; reads back as None.
        assert not reader.contains("platform/sensors/vis_camera/extrinsics")


def test_vessel_sensor_roster_round_trip(tmp_path: Path) -> None:
    """Round-trips a vessel sensor roster, mirroring the platform section."""
    path = tmp_path / "bundle.h5"
    usbl = VesselSensor(
        key="usbl_linkquest_transceiver",
        message_topics=[],
        identity=SensorIdentity(
            label="USBL", vendor="LinkQuest", product="TrackLink", type="usbl"
        ),
        extrinsics=SensorExtrinsics(
            locx=0.0, locy=0.0, locz=-1.0, rotx=0.0, roty=0.0, rotz=0.0
        ),
        calibration=None,
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.vessel.write_identity(VesselIdentity(vessel_name="RV Linnaeus"))
        writer.vessel.write_sensors([usbl])

    with open_deployment_bundle_reader(path) as reader:
        assert reader.vessel.identity() == VesselIdentity(
            vessel_name="RV Linnaeus"
        )
        assert reader.vessel.sensor_keys() == ["usbl_linkquest_transceiver"]
        assert reader.vessel.sensors() == [usbl]


def test_raw_telemetry_round_trip_and_window(tmp_path: Path) -> None:
    """Round-trips a raw telemetry table and narrows a read with a window."""
    path = tmp_path / "bundle.h5"
    start = datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)
    timestamps = [start + timedelta(seconds=index) for index in range(5)]
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "sensor_key": ["dvl_teledyne_navigator"] * 5,
            "message_topic": ["RDI"] * 5,
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.telemetry.raw.write("dvl_teledyne_navigator", "RDI", frame)

    with open_deployment_bundle_reader(path) as reader:
        assert reader.telemetry.raw.topics() == [
            ("dvl_teledyne_navigator", "RDI")
        ]
        assert reader.telemetry.raw.sensor_keys() == ["dvl_teledyne_navigator"]

        full = reader.telemetry.raw.read("dvl_teledyne_navigator", "RDI")
        assert len(full) == 5

        class _Window:
            start: datetime | None = timestamps[1]
            end: datetime | None = timestamps[3]

        windowed = reader.telemetry.raw.read(
            "dvl_teledyne_navigator", "RDI", window=_Window()
        )
        assert windowed["value"].tolist() == [2.0, 3.0, 4.0]


def test_processed_telemetry_append_replace_and_provenance(
    tmp_path: Path,
) -> None:
    """Appends processed telemetry in two chunks, then replaces it, with
    provenance written independently of the message writes."""
    path = tmp_path / "bundle.h5"
    start = datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)
    first_chunk = pd.DataFrame(
        {
            "timestamp": [start, start + timedelta(seconds=1)],
            "message_topic": ["RDI", "RDI"],
            "value": [1.0, 2.0],
        }
    )
    second_chunk = pd.DataFrame(
        {
            "timestamp": [start + timedelta(seconds=2)],
            "message_topic": ["RDI"],
            "value": [3.0],
        }
    )
    replacement = pd.DataFrame(
        {
            "timestamp": [start],
            "message_topic": ["RDI"],
            "value": [99.0],
        }
    )
    provenance = ProcessedProvenance(
        run_datetime=datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc)
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.telemetry.processed.append_messages(
            "dvl_teledyne_navigator", "RDI", first_chunk
        )
        writer.telemetry.processed.append_messages(
            "dvl_teledyne_navigator", "RDI", second_chunk
        )
        writer.telemetry.processed.write_provenance(
            "dvl_teledyne_navigator", "RDI", provenance
        )

    with open_deployment_bundle_reader(path) as reader:
        appended = reader.telemetry.processed.read(
            "dvl_teledyne_navigator", "RDI"
        )
        assert appended["value"].tolist() == [1.0, 2.0, 3.0]
        assert (
            reader.telemetry.processed.provenance(
                "dvl_teledyne_navigator", "RDI"
            )
            == provenance
        )

    with open_deployment_bundle_writer(path) as writer:
        writer.telemetry.processed.replace_messages(
            "dvl_teledyne_navigator", "RDI", replacement
        )

    with open_deployment_bundle_reader(path) as reader:
        replaced = reader.telemetry.processed.read(
            "dvl_teledyne_navigator", "RDI"
        )
        assert replaced["value"].tolist() == [99.0]
        # provenance is untouched by replace_messages
        assert (
            reader.telemetry.processed.provenance(
                "dvl_teledyne_navigator", "RDI"
            )
            == provenance
        )


def test_telemetry_section_topics_union(tmp_path: Path) -> None:
    """`telemetry.topics()` unions the raw and processed topic sets."""
    path = tmp_path / "bundle.h5"
    start = datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)
    raw_frame = pd.DataFrame(
        {
            "timestamp": [start],
            "sensor_key": ["dvl_teledyne_navigator"],
            "message_topic": ["RDI"],
        }
    )
    processed_frame = pd.DataFrame(
        {"timestamp": [start], "message_topic": ["DEPTH"]}
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.telemetry.raw.write("dvl_teledyne_navigator", "RDI", raw_frame)
        writer.telemetry.processed.append_messages(
            "_derived", "DEPTH", processed_frame
        )

    with open_deployment_bundle_reader(path) as reader:
        assert reader.telemetry.topics() == [
            ("_derived", "DEPTH"),
            ("dvl_teledyne_navigator", "RDI"),
        ]


def test_metocean_round_trip_and_enumeration(tmp_path: Path) -> None:
    """Round-trips a metocean table and enumerates providers/variables."""
    path = tmp_path / "bundle.h5"
    frame = pd.DataFrame(
        {
            "timestamp": [datetime(2023, 10, 21, 3, 0, 0, tzinfo=timezone.utc)],
            "sea_level": [0.42],
        }
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.metocean.write("worldtides", "sea_level", frame)

    with open_deployment_bundle_reader(path) as reader:
        assert reader.metocean.providers() == ["worldtides"]
        assert reader.metocean.variables("worldtides") == ["sea_level"]
        read_back = reader.metocean.read("worldtides", "sea_level")
        assert read_back["sea_level"].tolist() == [0.42]


def test_escape_hatch(tmp_path: Path) -> None:
    """`keys`/`contains`/`row_count`/`read_table` expose the raw store."""
    path = tmp_path / "bundle.h5"
    identity = DeploymentIdentity(
        deployment_label="qc2hyd_20231021T032349Z",
        deployment_datetime=datetime(
            2023, 10, 21, 3, 23, 49, tzinfo=timezone.utc
        ),
    )

    with open_deployment_bundle_writer(path) as writer:
        writer.write_header(_header())
        writer.deployment.write_identity(identity)

    with open_deployment_bundle_reader(path) as reader:
        assert "/deployment/identity" in reader.keys()
        assert reader.contains("deployment/identity")
        assert not reader.contains("deployment/metadata")
        assert reader.row_count("deployment/identity") == 1
        assert len(reader.read_table("deployment/identity")) == 1
