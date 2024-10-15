#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r23m7ms0_20100606_001908_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23m7ms0_20100606_001908"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r23m7ms0_20120601_070118_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23m7ms0_20120601_070118"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r23m7ms0_20140616_044549_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r23m7ms0_20140616_044549"
