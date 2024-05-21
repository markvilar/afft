#!/usr/bin/bash

CAMERAS="$HOME/data/acfr_revisits_processed/acfr_renav_files/qd61g27j_20100421_022145_stereo_pose_est.data"
SELECTION="$HOME/data/acfr_revisits_processed/acfr_camera_labels/qd61g27j_20100421_022145_camera_labels.txt"

poetry run raft-cli format_cameras $CAMERAS --selection $SELECTION
