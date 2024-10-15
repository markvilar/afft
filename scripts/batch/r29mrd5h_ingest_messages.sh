#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd5h_20090612_225306_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd5h_20090612_225306"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd5h_20090613_100254_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd5h_20090613_100254"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd5h_20110612_033752_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd5h_20110612_033752"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd5h_20130611_002419_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd5h_20130611_002419"
