#!/usr/bin/bash

REFERENCE_DIR=/home/martin/data/acfr_debug
SELECTION_DIR=/home/martin/data/geomedia/export

DEPLOYMENT=qdch0ftq/r20210315_034028_SS10_geebank_15m_out

POSE_FILE=$REFERENCE_DIR/$DEPLOYMENT/poses/renav20210528_1352/stereo_pose_est.data
SELECTION_FILE=$SELECTION_DIR/$DEPLOYMENT/r20210315_034028_labels.txt

python process_poses.py $POSE_FILE $SELECTION_FILE
