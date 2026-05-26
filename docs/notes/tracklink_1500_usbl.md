# LinkQuest TrackLink 1500 USBL — Research Notes

## Overview

The TrackLink 1500 is an integrated USBL (Ultra Short Baseline) acoustic tracking and
high-speed communication system made by LinkQuest Inc. It tracks underwater targets
(e.g. AUVs) from a surface vessel and logs range, bearing, and ship attitude.

**Key specs (1500 series):**
- Tracking range: up to 1000 m (long-range variant) / 500 m (standard)
- Bearing accuracy: up to 0.25°
- Outputs: range, bearing, depth, GPS position, acoustic communication data

## Output Data Fields

The LQMODEM log message (as parsed in `sirius/message_parsers.py`) contains:

| Field | Description |
|---|---|
| `timestamp` | Message timestamp |
| `latitude` | Ship GPS latitude |
| `longitude` | Ship GPS longitude |
| `heading` | Ship heading (degrees) |
| `roll` | Ship roll (degrees) |
| `pitch` | Ship pitch (degrees) |
| `bearing` | Bearing from ship to target (AUV) |
| `range` | Slant range from ship to target (m) |
| `time` | Internal device time |

The 5000-series manual (same product family) documents a similar raw output with fields:
target number, time, target bearing, slant range, X offset, Y offset, Z offset.

## Bearing Convention

**Raw transceiver output:** vessel-relative (relative to the transceiver/bow direction).

**After software calibration:** the TrackLink Navigator software applies a "Heading Offset"
to convert from transceiver-relative to absolute compass bearing before logging.

**Conclusion for LQMODEM logs:** the logged `bear` field is treated as **absolute compass
bearing** (degrees from north, clockwise). This is supported by the data:

- In a sample sequence, ship heading drops ~64° (205° → 141°, a port turn).
- If bearing were vessel-relative, a near-stationary target bearing would shift +64°.
- Instead, bearing drops ~41° (259° → 218°), consistent with absolute bearing as
  the AUV swims away to the south.

The processor implements a configurable `bearing_reference` parameter
(`"absolute"` | `"relative"`) in case this assumption needs overriding.

## Position Reconstruction

The TrackLink gives slant range + bearing but **not** the AUV's absolute lat/lon
directly. To resolve the full 3D position, depth from the pressure sensor is required:

```
horizontal_range = sqrt(slant_range² - depth²)
target_lat, target_lon = project(ship_lat, ship_lon, bearing, horizontal_range)
```

This is implemented in the `usbl_resolve_position` processor, which is a joint processor
taking both the `lqmodem` and `parosci_pressure` tables as inputs.

## Sources

- [TrackLink 1500 product page](https://www.link-quest.com/html/tracklink_1500.htm)
- [TrackLink 1500 datasheet (PDF)](https://www.link-quest.com/html/tl1500_lr.pdf)
- [TrackLink 5000 Series User Manual (ManualsLib)](https://www.manualslib.com/manual/1610048/Linkquest-Tracklink-5000-Series.html)
- [DiveWorks LinkQuest USBL brochure](https://www.diveworks.com.au/wp-content/uploads/2023/10/DWS-LinkQuest-USBL-Tracking-System.pdf)
- [LinkQuest TrackLink USBL Systems overview](https://www.link-quest.com/html/intro2.htm)
