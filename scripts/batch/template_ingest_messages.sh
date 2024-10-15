#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/FILE.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "LABEL"

