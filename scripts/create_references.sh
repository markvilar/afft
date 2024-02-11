#!/usr/bin/bash

INDEX_DIR=/home/martin/data/acfr_indices
DATA_DIR=/home/martin/data/acfr_debug
OUTPUT_DIR=/home/martin/test/camera_references

python format_cameras.py \
    $INDEX_DIR/qdch0ftq_index.json \
    $DATA_DIR/qdch0ftq \
    $OUTPUT_DIR
