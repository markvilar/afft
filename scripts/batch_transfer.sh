#!/usr/bin/bash

python tools/transfer_acfr.py \
    --endpoints ./config/endpoints/acfr_raw.ini \
    --targets ./config/jobs/raw_data.toml \
    --dry-run
