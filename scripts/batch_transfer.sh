#!/usr/bin/bash

DESTINATION=local:/home/martin/test/transfer

QUERIES=/home/martin/data/geomedia/group_files

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/RAW_DATA \
    --destination $DESTINATION \
    --targets ./config/targets/raw.toml \
    --references $QUERIES/qd61g27j.json \
    --dry-run
