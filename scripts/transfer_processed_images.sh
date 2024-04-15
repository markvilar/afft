#!/usr/bin/bash

DESTINATION=local:/media/martin/barracuda/data/acfr_raw/groups

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
    --searches $QUERIES/r29kz9dg.json

python tools/transfer_acfr.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION \
    --routes ./config/routes/processed_images.toml \
    --searches $QUERIES/r29kz9ff.json

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


