"""Position resolution and orchestration for the Evologics S2C R 18/34 USBL."""

import numpy as np
import pandas as pd

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
    config: EvologicsProcessingConfig = EvologicsProcessingConfig(),
) -> pd.DataFrame:
    """Convert Evologics USBL data to the unified USBL output schema.

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
          target_horizontal_range, target_inclination_angle,
          horizontal_position_std, depth_position_std, evologics_accuracy,
          usbl_extrinsics_locx, usbl_extrinsics_locy, usbl_extrinsics_locz,
          usbl_extrinsics_rotx, usbl_extrinsics_roty, usbl_extrinsics_rotz.
    Removes: accuracy (renamed to evologics_accuracy).

    Arguments
    ---------
    usbl: Parsed Evologics USBL DataFrame with USBL-Frame target_x/y/z.
    config: Processing configuration with optional extrinsics and uncertainty values.

    Returns
    -------
    DataFrame conforming to the unified USBL output schema.
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

    extrinsics: EvologicsTransceiverExtrinsics = (
        config.extrinsics
        if config.extrinsics is not None
        else EvologicsTransceiverExtrinsics()
    )

    # Apply frame flip (USBL-Frame → intermediate aligned with vessel axes).
    target_flipped: NDArray[np.float64] = (_RFU_TO_FRD @ target_xyz_usbl.T).T

    # Apply extrinsics rotation and translation to reach Vessel-Frame.
    target_xyz_vessel: NDArray[np.float64] = extrinsics.transform.apply(
        target_flipped
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

    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["horizontal_position_std"] = config.horizontal_position_std
    result["depth_position_std"] = config.depth_position_std
    result["usbl_extrinsics_locx"] = extrinsics.locx
    result["usbl_extrinsics_locy"] = extrinsics.locy
    result["usbl_extrinsics_locz"] = extrinsics.locz
    result["usbl_extrinsics_rotx"] = extrinsics.rotx
    result["usbl_extrinsics_roty"] = extrinsics.roty
    result["usbl_extrinsics_rotz"] = extrinsics.rotz
    result = result.rename(columns={"accuracy": "evologics_accuracy"})

    return result
