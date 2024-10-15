#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r234xgje_20100604_230524_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r234xgje_20100604_230524"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r234xgje_20120530_064545_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r234xgje_20120530_064545"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r234xgje_20140616_205232_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r234xgje_20140616_205232"
