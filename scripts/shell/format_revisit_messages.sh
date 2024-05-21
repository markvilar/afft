#!/usr/bin/bash

INPUT_DIR="/home/martin/data/acfr_revisits_unprocessed/acfr_measurements_unprocessed"
OUTPUT_DIR="/home/martin/data/acfr_revisits_processed/acfr_message_files"

TASK_CONFIG="config/messages/r23685bc_messages.toml"

poetry run raft-cli merge_messages $TASK_CONFIG $INPUT_DIR $OUTPUT_DIR
