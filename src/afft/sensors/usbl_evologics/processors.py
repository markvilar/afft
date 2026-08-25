"""Position resolution and orchestration for the Evologics S2C R 18/34 USBL."""

import numpy as np
import pandas as pd
import pymap3d
from scipy.spatial.transform import Rotation

from numpy.typing import NDArray

from .types import (
    EvologicsProcessingConfig,
    EvologicsTransceiverExtrinsics,
)

# Permutation from Right-Forward-Up (USBL frame) to Forward-Right-Down (vessel frame).
_RFU_TO_FRD: NDArray[np.float64] = np.array(
    [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
    dtype=np.float64,
)


def process_evologics_usbl(
    usbl: pd.DataFrame,
    extrinsics: EvologicsTransceiverExtrinsics | None = None,
    config: EvologicsProcessingConfig = EvologicsProcessingConfig(),
) -> pd.DataFrame:
    """Convert Evologics USBL data to the USBL output schema.

    The schema is a core shared with the other USBL sensors, plus the
    sensor-specific `evologics_accuracy`.

    Applies the USBL-Frame → Vessel-Frame transformation to target_x/y/z,
    derives geometric quantities, assigns deployment-calibrated uncertainty
    values, and renames the on-board accuracy estimate.

    The transformation follows eq. 3.10 from the Evologics USBL maths document:

        X_vt = X_vu + R_vu · F · X_ut

    where X_ut is the target in USBL-Frame, F is the constant axis-flip matrix,
    R_vu is the extrinsics rotation, and X_vu is the transceiver translation in
    Vessel-Frame. When no extrinsics are provided only the frame flip is applied.

    Adds: target_x_sensor, target_y_sensor, target_z_sensor (USBL-Frame),
          target_x_vessel, target_y_vessel, target_z_vessel (Vessel-Frame),
          target_depth, target_latitude, target_longitude, target_height,
          target_horizontal_range, target_inclination_angle,
          horizontal_position_std, depth_position_std, evologics_accuracy,
          usbl_extrinsics_locx, usbl_extrinsics_locy, usbl_extrinsics_locz,
          usbl_extrinsics_rotx, usbl_extrinsics_roty, usbl_extrinsics_rotz,
          usbl_extrinsics_applied, usbl_extrinsics_rotation_units.
    Removes: accuracy (renamed to evologics_accuracy).

    target_depth, target_latitude, and target_longitude are the modem-reported
    values, assigned explicitly. target_height is the WGS84 ellipsoidal height
    derived from the ship position, ship attitude, and transceiver extrinsics
    via the NED → geodetic chain (pymap3d.ned2geodetic).

    Extrinsics rotations are recorded in the output in degrees, so that every
    angle in the resulting table shares one unit, with
    `usbl_extrinsics_rotation_units` stating it explicitly.

    Arguments
    ---------
    usbl: Parsed Evologics USBL DataFrame with USBL-Frame target_x/y/z.
    extrinsics: Transceiver extrinsics in the ship body frame. When None, no
        extrinsics correction is applied -- only the USBL-Frame flip -- and
        `usbl_extrinsics_applied` is False. Omit it for deployments whose
        readings were already corrected upstream.
    config: Processing configuration with uncertainty values.

    Returns
    -------
    DataFrame conforming to the USBL output schema.
    """
    result: pd.DataFrame = usbl.copy()

    target_xyz_usbl: NDArray[np.float64] = np.column_stack(
        [
            usbl["target_x"].to_numpy(),
            usbl["target_y"].to_numpy(),
            usbl["target_z"].to_numpy(),
        ]
    )

    # Slant range and inclination from USBL-Frame geometry (before transformation).
    slant_range: NDArray[np.float64] = np.linalg.norm(target_xyz_usbl, axis=1)
    # USBL Z is positive up; negate to get depth below transceiver (positive down).
    depth_rel: NDArray[np.float64] = -target_xyz_usbl[:, 2]
    target_inclination_angle: NDArray[np.float64] = np.degrees(
        np.arcsin(np.clip(depth_rel / slant_range, -1.0, 1.0))
    )

    extrinsics_applied: bool = extrinsics is not None
    if extrinsics is None:
        extrinsics = EvologicsTransceiverExtrinsics()

    # Apply frame flip (USBL-Frame → intermediate aligned with vessel axes).
    target_flipped: NDArray[np.float64] = (_RFU_TO_FRD @ target_xyz_usbl.T).T

    # Apply extrinsics rotation and translation to reach Vessel-Frame.
    target_xyz_vessel: NDArray[np.float64] = extrinsics.transform.apply(
        target_flipped
    )

    # Resolve the target's WGS84 ellipsoidal height via the NED → geodetic chain.
    ship_attitudes_ypr: NDArray[np.float64] = np.column_stack(
        [
            usbl["ship_heading"].to_numpy(),
            usbl["ship_pitch"].to_numpy(),
            usbl["ship_roll"].to_numpy(),
        ]
    )
    R_ship: Rotation = Rotation.from_euler(
        "zyx", ship_attitudes_ypr, degrees=True
    )
    # Transceiver NED offset from the ship reference point, and target NED offset
    # from the transceiver (extrinsics rotation only, then ship attitude).
    transceiver_ned: NDArray[np.float64] = R_ship.apply(
        np.tile(extrinsics.translation, (len(usbl), 1))
    )
    target_ned: NDArray[np.float64] = R_ship.apply(
        extrinsics.rotation.apply(target_flipped)
    )
    transceiver_lat: NDArray[np.float64]
    transceiver_lon: NDArray[np.float64]
    transceiver_alt: NDArray[np.float64]
    transceiver_lat, transceiver_lon, transceiver_alt = pymap3d.ned2geodetic(
        transceiver_ned[:, 0],
        transceiver_ned[:, 1],
        transceiver_ned[:, 2],
        usbl["ship_latitude"].to_numpy(),
        usbl["ship_longitude"].to_numpy(),
        np.zeros(len(usbl)),
    )
    target_height: NDArray[np.float64]
    _, _, target_height = pymap3d.ned2geodetic(
        target_ned[:, 0],
        target_ned[:, 1],
        target_ned[:, 2],
        transceiver_lat,
        transceiver_lon,
        transceiver_alt,
    )

    target_horizontal_range: NDArray[np.float64] = np.sqrt(
        target_xyz_vessel[:, 0] ** 2 + target_xyz_vessel[:, 1] ** 2
    )

    result["target_x_sensor"] = target_xyz_usbl[:, 0]
    result["target_y_sensor"] = target_xyz_usbl[:, 1]
    result["target_z_sensor"] = target_xyz_usbl[:, 2]
    result["target_x_vessel"] = target_xyz_vessel[:, 0]
    result["target_y_vessel"] = target_xyz_vessel[:, 1]
    result["target_z_vessel"] = target_xyz_vessel[:, 2]

    result["target_depth"] = usbl["target_depth"]
    result["target_latitude"] = usbl["target_latitude"]
    result["target_longitude"] = usbl["target_longitude"]
    result["target_height"] = target_height

    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["horizontal_position_std"] = config.horizontal_position_std
    result["depth_position_std"] = config.depth_position_std
    result["usbl_extrinsics_locx"] = extrinsics.locx
    result["usbl_extrinsics_locy"] = extrinsics.locy
    result["usbl_extrinsics_locz"] = extrinsics.locz
    result["usbl_extrinsics_rotx"] = np.degrees(extrinsics.rotx)
    result["usbl_extrinsics_roty"] = np.degrees(extrinsics.roty)
    result["usbl_extrinsics_rotz"] = np.degrees(extrinsics.rotz)
    result["usbl_extrinsics_applied"] = extrinsics_applied
    result["usbl_extrinsics_rotation_units"] = "degrees"
    result = result.rename(columns={"accuracy": "evologics_accuracy"})

    return result
