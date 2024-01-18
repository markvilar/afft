#!/usr/bin/bash

DESTINATION=local:/media/martin/lacie/data/acfr_processed_simple/groups
QUERIES=/home/martin/data/geomedia/group_queries

# -----------------------------------------------------------------------------
# ---- WAS --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/qd61g27j.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/qdc5ghs3.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/qdch0ftq.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/qdchdmy1.json

# -----------------------------------------------------------------------------
# ---- SCO --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/qtqxshxs.json

# -----------------------------------------------------------------------------
# ---- SEQ --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r7jjskxq.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r7jjss8n.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r7jjssbh.json

