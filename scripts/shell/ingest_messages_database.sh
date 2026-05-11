#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"

SOURCE="${MESSAGE_DIR}/r23685bc_20100605_021022_messages.txt"
DESTINATION=
CONFIG="./config/protocol/protocol_v1.toml"

uv run afft messages parse-messages \
  "${MESSAGE_DIR}/r23685bc_20100605_021022_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23685bc_20100605_021022"

uv run afft messages parse-messages \
  "${MESSAGE_DIR}/r23685bc_20120530_233021_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23685bc_20120530_233021"

uv run afft messages parse-messages \
  "${MESSAGE_DIR}/r23685bc_20140616_225022_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23685bc_20140616_225022"

