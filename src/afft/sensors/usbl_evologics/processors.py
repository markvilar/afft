"""Position resolution and orchestration for the Evologics S2C R 18/34 USBL."""

import numpy as np
import pandas as pd

from numpy.typing import NDArray

from .types import EvologicsProcessingConfig

# Constant frame flip: USBL-Frame (X=right, Y=fwd, Z=up) → Vessel-Frame (X=fwd, Y=stbd, Z=down).
_USBL_TO_VESSEL: NDArray[np.float64] = np.array(
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
          usbl_extrinsics_x, usbl_extrinsics_y, usbl_extrinsics_z,
          usbl_extrinsics_phi, usbl_extrinsics_theta, usbl_extrinsics_psi.
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

    # Apply frame flip (USBL-Frame → intermediate aligned with vessel axes).
    target_flipped: NDArray[np.float64] = (
        _USBL_TO_VESSEL @ target_xyz_usbl.T
    ).T

    # Apply extrinsics rotation and translation to reach Vessel-Frame.
    if config.extrinsics is not None:
        target_xyz_vessel: NDArray[np.float64] = (
            config.extrinsics.transform.apply(target_flipped)
        )
    else:
        target_xyz_vessel = target_flipped

    target_horizontal_range: NDArray[np.float64] = np.sqrt(
        target_xyz_vessel[:, 0] ** 2 + target_xyz_vessel[:, 1] ** 2
    )

    result["target_x_sensor"] = target_xyz_usbl[:, 0]
    result["target_y_sensor"] = target_xyz_usbl[:, 1]
    result["target_z_sensor"] = target_xyz_usbl[:, 2]
    result["target_x_vessel"] = target_xyz_vessel[:, 0]
    result["target_y_vessel"] = target_xyz_vessel[:, 1]
    result["target_z_vessel"] = target_xyz_vessel[:, 2]
    extrinsics_x: float = (
        config.extrinsics.x if config.extrinsics is not None else 0.0
    )
    extrinsics_y: float = (
        config.extrinsics.y if config.extrinsics is not None else 0.0
    )
    extrinsics_z: float = (
        config.extrinsics.z if config.extrinsics is not None else 0.0
    )
    extrinsics_phi: float = (
        config.extrinsics.phi if config.extrinsics is not None else 0.0
    )
    extrinsics_theta: float = (
        config.extrinsics.theta if config.extrinsics is not None else 0.0
    )
    extrinsics_psi: float = (
        config.extrinsics.psi if config.extrinsics is not None else 0.0
    )

    result["target_horizontal_range"] = target_horizontal_range
    result["target_inclination_angle"] = target_inclination_angle
    result["horizontal_position_std"] = config.horizontal_position_std
    result["depth_position_std"] = config.depth_position_std
    result["usbl_extrinsics_x"] = extrinsics_x
    result["usbl_extrinsics_y"] = extrinsics_y
    result["usbl_extrinsics_z"] = extrinsics_z
    result["usbl_extrinsics_phi"] = extrinsics_phi
    result["usbl_extrinsics_theta"] = extrinsics_theta
    result["usbl_extrinsics_psi"] = extrinsics_psi
    result = result.rename(columns={"accuracy": "evologics_accuracy"})

    return result
