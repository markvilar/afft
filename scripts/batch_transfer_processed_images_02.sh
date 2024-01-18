#!/usr/bin/bash

DESTINATION=local:/media/martin/lacie/data/acfr_processed_simple/groups
QUERIES=/home/martin/data/geomedia/group_queries

# -----------------------------------------------------------------------------
# ---- TAS --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r234xgje.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r23685bc.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r23m7ms0.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r29mrd12.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r29mrd5h.json























