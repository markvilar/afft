#!/usr/bin/bash

DESTINATION=local:/media/martin/barracuda/data/acfr_raw/groups

QUERIES=/home/martin/data/geomedia/group_queries

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed.toml \
    --searches $QUERIES/qtqxshxs.json
