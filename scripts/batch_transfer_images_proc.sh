#!/usr/bin/bash

SOURCE=acfr_archipelago:/media/water/PROCESSED_DATA
DESTINATION=local:/media/martin/lacie/data/acfr_processed_simple
QUERIES=/home/martin/data/geomedia/search_objects

# -----------------------------------------------------------------------------
# ---- WAS --------------------------------------------------------------------
# -----------------------------------------------------------------------------

exit 0

python tools/transfer_search_objects.py \
    --source $SOURCE \
    --destination $DESTINATION/qd61g27j \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/qd61g27j_search_objects.json

python tools/transfer_search_objects.py \
    --source $SOURCE \
    --destination $DESTINATION/qdc5ghs3 \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/qdc5ghs3_search_objects.json

 # NOTE: Bug with last deployment here
 python tools/transfer_search_objects.py \
     --source $SOURCE \
     --destination $DESTINATION/qdch0ftq \
     --routes ./config/routes/images_processed.toml \
     --searches $QUERIES/qdch0ftq_search_objects.json
 
 # NOTE: Bug with last deployment here
 python tools/transfer_search_objects.py \
     --source $SOURCE \
     --destination $DESTINATION/qdchdmy1 \
     --routes ./config/routes/images_processed.toml \
     --searches $QUERIES/qdchdmy1_search_objects.json

# -----------------------------------------------------------------------------
# ---- SCO --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_search_objects.py \
    --source $SOURCE \
    --destination $DESTINATION/qtqxshxs \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/qtqxshxs_search_objects.json

# -----------------------------------------------------------------------------
# ---- TAS --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r234xgje \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r234xgje_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r23685bc \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r23685bc_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r23m7ms0 \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r23m7ms0_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r29mrd12 \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r29mrd12_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r29mrd5h \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r29mrd5h_search_objects.json

# -----------------------------------------------------------------------------
# ---- SEQ --------------------------------------------------------------------
# -----------------------------------------------------------------------------

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r7jjskxq \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r7jjskxq_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r7jjss8n \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r7jjss8n_search_objects.json

python tools/transfer_search_objects.py \
    --source acfr_archipelago:/media/water/PROCESSED_DATA \
    --destination $DESTINATION/r7jjssbh \
    --routes ./config/routes/images_processed.toml \
    --searches $QUERIES/r7jjssbh_search_objects.json
