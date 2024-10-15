#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qtqxshxs_20110815_102540_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qtqxshxs_20110815_102540"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qtqxshxs_20150327_015552_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qtqxshxs_20150327_015552"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qtqxshxs_20150328_000850_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qtqxshxs_20150328_000850"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qtqxshxs_20150328_042551_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qtqxshxs_20150328_042551"
