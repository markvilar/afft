#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r7jjskxq_20101023_210332_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r7jjskxq_20101023_210332"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r7jjskxq_20121013_060425_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r7jjskxq_20121013_060425"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r7jjskxq_20131022_004934_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r7jjskxq_20131022_004934"
