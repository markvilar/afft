#!/usr/bin/bash

INDEX_DIR=/media/martin/lacie/data/acfr_indices
DATA_DIR=/media/martin/barracuda/data/acfr_raw/groups
OUTPUT_DIR=/media/martin/lacie/data/acfr_cameras

python format_cameras.py \
    $INDEX_DIR/qdch0ftq_index.json \
    $DATA_DIR/qdch0ftq \
    $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/qdc5ghs3_index.json \
    $DATA_DIR/qdc5ghs3 $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/qdch0ftq_index.json \
    $DATA_DIR/qdch0ftq $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/qdchdmy1_index.json \
    $DATA_DIR/qdchdmy1 $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/qtqxshxs_index.json \
    $DATA_DIR/qtqxshxs $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r7jjskxq_index.json \
    $DATA_DIR/r7jjskxq $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r7jjss8n_index.json \
    $DATA_DIR/r7jjss8n $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r7jjssbh_index.json \
    $DATA_DIR/r7jjssbh $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r23m7ms0_index.json \
    $DATA_DIR/r23m7ms0 $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r29mrd5h_index.json \
    $DATA_DIR/r29mrd5h $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r29mrd12_index.json \
    $DATA_DIR/r29mrd12 $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r234xgje_index.json \
    $DATA_DIR/r234xgje $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/r23685bc_index.json \
    $DATA_DIR/r23685bc $OUTPUT_DIR

python format_cameras.py $INDEX_DIR/qd61g27j_index.json \
    $DATA_DIR/qd61g27j $OUTPUT_DIR
