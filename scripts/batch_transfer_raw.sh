#!/usr/bin/bash

DESTINATION=local:/media/martin/barracuda/data/acfr_raw/groups

QUERIES=/home/martin/data/geomedia/group_files

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/RAW_DATA \
    --destination $DESTINATION \
    --targets ./config/targets/raw.toml \
    --references $QUERIES/r23685bc.json
