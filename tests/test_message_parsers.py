"""Tests for SEABED message parsing."""

from datetime import datetime, timezone

from afft.seabed.message_parsers import (
    parse_aanderaa_ctd_message_v1,
    parse_battery_message_v1,
    parse_ecopuck_message_v1,
    parse_evologics_modem_message_v1,
    parse_gps_gsv_message_v1,
    parse_gps_rmc_message_v1,
    parse_image_message_v1,
    parse_lq_modem_message_v1,
    parse_micron_sonar_message_v1,
    parse_obstacle_avoidance_sonar_message_v1,
    parse_parosci_pressure_message_v1,
    parse_seabird_ctd_message_v1,
    parse_teledyne_dvl_message_v1,
    parse_thruster_message_v1,
)


def test_parse_thruster_message_v1() -> None:
    line = "THR_PORT:  1495772756.256        RPM:22.15 A:0.1800 V:46.50 T:51.00"
    message = parse_thruster_message_v1(line)

    assert message.header.topic == "THR_PORT"
    assert message.header.timestamp == datetime.fromtimestamp(
        1495772756.256, tz=timezone.utc
    )
    assert message.payload.label == "thruster_portside"
    assert message.payload.rpm == 22.15
    assert message.payload.current == 0.1800
    assert message.payload.voltage == 46.50
    assert message.payload.temperature == 51.00


def test_parse_teledyne_dvl_message_v1() -> None:
    line = (
        "RDI: 1495772707.612 alt:1.745 r1:1.930 r2:1.260 r3:2.390 r4:1.400 "
        "h:300.660 p:2.890 r:-1.220 vx:0.072 vy:0.479 vz:0.026 nx:-52.674 "
        "ny:1526.445 nz:-96.520 COG:0.149 SOG:0.484 bt_status:0 h_true:300.660 "
        "p_gimbal:2.889 sv:1530.000"
    )
    message = parse_teledyne_dvl_message_v1(line)

    assert message.header.topic == "RDI"
    assert message.payload.altitude == 1.745
    assert message.payload.range_01 == 1.930
    assert message.payload.range_02 == 1.260
    assert message.payload.range_03 == 2.390
    assert message.payload.range_04 == 1.400
    assert message.payload.heading == 300.660
    assert message.payload.pitch == 2.890
    assert message.payload.roll == -1.220
    assert message.payload.velocity_x == 0.072
    assert message.payload.velocity_y == 0.479
    assert message.payload.velocity_z == 0.026
    assert message.payload.dmg_x == -52.674
    assert message.payload.dmg_y == 1526.445
    assert message.payload.dmg_z == -96.520
    assert message.payload.course_over_ground == 0.149
    assert message.payload.speed_over_ground == 0.484
    assert message.payload.bottom_track_status == 0
    assert message.payload.true_heading == 300.660
    assert message.payload.gimbal_pitch == 2.889
    assert message.payload.sound_velocity == 1530.000


def test_parse_parosci_pressure_message_v1() -> None:
    line = "PAROSCI:  1495772707.641        17.4117"
    message = parse_parosci_pressure_message_v1(line)

    assert message.header.topic == "PAROSCI"
    assert message.payload.depth == 17.4117


def test_parse_seabird_ctd_message_v1() -> None:
    line = (
        "SEABIRD:  1335747601.584        cond:5.226 temp:23.975 sal:35.195 "
        "pres:0.000 sos:1532.112"
    )
    message = parse_seabird_ctd_message_v1(line)

    assert message.header.topic == "SEABIRD"
    assert message.payload.conductivity == 5.226
    assert message.payload.temperature == 23.975
    assert message.payload.salinity == 35.195
    assert message.payload.pressure == 0.000
    assert message.payload.sound_velocity == 1532.112


def test_parse_aanderaa_ctd_message_v1() -> None:
    line = (
        "AANDERAA_4319:  1615780800.039        cond:5.250 temp:24.367 "
        "sal:35.064 pres:0.000 sos:1532.956"
    )
    message = parse_aanderaa_ctd_message_v1(line)

    assert message.header.topic == "AANDERAA_4319"
    assert message.payload.conductivity == 5.250
    assert message.payload.temperature == 24.367
    assert message.payload.salinity == 35.064
    assert message.payload.pressure == 0.000
    assert message.payload.sound_velocity == 1532.956


def test_parse_image_message_v1() -> None:
    line = (
        "VIS: 1495772756.134  [1495772755.415039] "
        "PR_20170526_042555_415_LC16.tif exp: 4121"
    )
    message = parse_image_message_v1(line)

    assert message.header.topic == "VIS"
    assert message.payload.label == "PR_20170526_042555_415_LC16"
    assert message.payload.filename == "PR_20170526_042555_415_LC16.tif"
    assert message.payload.trigger_time == datetime.fromtimestamp(
        1495772755.415039, tz=timezone.utc
    )
    assert message.payload.exposure_logged is True
    assert message.payload.exposure == 4121


def test_parse_gps_gsv_message_v1() -> None:
    line = "GPS_GSV:  1495774800.320 SV:14"
    message = parse_gps_gsv_message_v1(line)

    assert message.header.topic == "GPS_GSV"
    assert message.payload.satellites_in_view == 14


def test_parse_gps_rmc_message_v1() -> None:
    line = (
        "GPS_RMC:  1370910445.897 Lat:-41.253271667 S Lon:148.342691667 E  "
        "Bad:   0 A Spd:0.400 Crs:0.000 Mg:-1.000"
    )
    message = parse_gps_rmc_message_v1(line)

    assert message.header.topic == "GPS_RMC"
    assert message.payload.latitude == -41.253271667
    assert message.payload.longitude == 148.342691667
    assert message.payload.bad == 0
    assert message.payload.status == "A"
    assert message.payload.speed_knots == 0.400
    assert message.payload.course_over_ground == 0.000
    assert message.payload.magnetic_variation == -1.000


def test_parse_lq_modem_message_v1() -> None:
    line = (
        "LQMODEM: 1370910445.812 time:1370910464.000 Lat:-41.253475189 "
        "Lon:148.342895508 hdg:231.3 roll:-3.5 pitch:1.7 bear:140.90 rng:25.10"
    )
    message = parse_lq_modem_message_v1(line)

    assert message.header.topic == "LQMODEM"
    assert message.payload.device_time == 1370910464.000
    assert message.payload.ship_latitude == -41.253475189
    assert message.payload.ship_longitude == 148.342895508
    assert message.payload.ship_heading == 231.3
    assert message.payload.ship_roll == -3.5
    assert message.payload.ship_pitch == 1.7
    assert message.payload.target_bearing_angle == 140.90
    assert message.payload.target_slant_range == 25.10


def test_parse_evologics_modem_message_v1() -> None:
    line = (
        "EVOLOGICS_FIX:  1495772673.026 target_lat:-28.813446502 "
        "target_lon:113.947151550  target_depth:12.357 accuracy:3.537 "
        "ship_lat:-28.812462645 ship_lon:113.946070301 ship_roll: -1.61 "
        "ship_pitch: -0.01 ship_heading:270.35 target_x:-54.63 "
        "target_y:-141.69 target_z: -4.48"
    )
    message = parse_evologics_modem_message_v1(line)

    assert message.header.topic == "EVOLOGICS_FIX"
    assert message.payload.target_latitude == -28.813446502
    assert message.payload.target_longitude == 113.947151550
    assert message.payload.target_depth == 12.357
    assert message.payload.accuracy == 3.537
    assert message.payload.ship_latitude == -28.812462645
    assert message.payload.ship_longitude == 113.946070301
    assert message.payload.ship_roll == -1.61
    assert message.payload.ship_pitch == -0.01
    assert message.payload.ship_heading == 270.35
    assert message.payload.target_x == -54.63
    assert message.payload.target_y == -141.69
    assert message.payload.target_z == -4.48


def test_parse_battery_message_v1() -> None:
    line = (
        "BATT: 1272423604.158  TimeLeft:481  PercentCharge:84  "
        "Current:-8.959000  Voltage:15.610000  Power:139.800003  Charging:0"
    )
    message = parse_battery_message_v1(line)

    assert message.header.topic == "BATT"
    assert message.payload.label == "battery"
    assert message.payload.time_left == 481
    assert message.payload.current == -8.959000
    assert message.payload.voltage == 15.610000
    assert message.payload.power == 139.800003
    assert message.payload.charge_percent == 84
    assert message.payload.charging is False


def test_parse_battery_message_v1_indexed_topic() -> None:
    line = (
        "BATT1: 1370912253.472  TimeLeft:0  PercentCharge:0  Current:0.000000 "
        " Voltage:0.000000  Power:0.000000  Charging:1"
    )
    message = parse_battery_message_v1(line)

    assert message.header.topic == "BATT1"
    assert message.payload.label == "battery_01"
    assert message.payload.charging is True


def test_parse_obstacle_avoidance_sonar_message_v1() -> None:
    line = "OAS:  1335747601.527  ProfRng:  4.42 PseudoAlt:  2.15 PseudoFwdDistance:  3.46"
    message = parse_obstacle_avoidance_sonar_message_v1(line)

    assert message.header.topic == "OAS"
    assert message.payload.profile_range == 4.42
    assert message.payload.profile_altitude == 2.15
    assert message.payload.pseudo_forward_distance == 3.46


def test_parse_micron_sonar_message_v1() -> None:
    line = (
        "MICRON:  1370912251.453  ProfRng:  9.83 PseudoAlt:  1.63 "
        "PseudoFwdDistance:  8.54 Angle:  3.17"
    )
    message = parse_micron_sonar_message_v1(line)

    assert message.header.topic == "MICRON"
    assert message.payload.profile_range == 9.83
    assert message.payload.profile_altitude == 1.63
    assert message.payload.pseudo_forward_distance == 8.54
    assert message.payload.angle == 3.17


def test_parse_micron_sonar_message_v1_returns_topic() -> None:
    line = (
        "MICRON_RETURNS:  1370912251.453  ProfRng:  9.83 "
        "PseudoAlt:-98765.00 PseudoFwdDistance:  9.83 Angle:  3.17"
    )
    message = parse_micron_sonar_message_v1(line)

    assert message.header.topic == "MICRON_RETURNS"
    assert message.payload.profile_altitude == -98765.00


def test_parse_ecopuck_message_v1() -> None:
    line = "ECOPUCK:  1495771206.411 chlor:0.686 bcksct:0.002504 cdom:0.601 temp:-10.00"
    message = parse_ecopuck_message_v1(line)

    assert message.header.topic == "ECOPUCK"
    assert message.payload.chlorophyll == 0.686
    assert message.payload.backscatter == 0.002504
    assert message.payload.cdom == 0.601
    assert message.payload.temperature == -10.00
