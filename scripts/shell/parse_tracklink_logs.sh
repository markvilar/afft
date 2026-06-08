#!/usr/bin/bash

SOURCE_DIR="/data/exos_01/acfr_tracklink_logs_v1_merged"
OUTPUT_DIR="/data/exos_01/acfr_tracklink_logs_v2_parsed"

for source_file in "${SOURCE_DIR}"/*_tracklink_log.txt; do
    label=$(basename "${source_file}" _tracklink_log.txt)
    output_file="${OUTPUT_DIR}/${label}_tracklink_fixes.csv"

    uv run afft sensors parse-tracklink-log \
        --source-file "${source_file}" \
        --output-file "${output_file}"
done
