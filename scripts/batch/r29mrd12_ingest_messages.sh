#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd12_20090613_010853_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd12_20090613_010853"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd12_20090613_104954_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd12_20090613_104954"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd12_20110612_045149_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd12_20110612_045149"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/r29mrd12_20130611_015335_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "r29mrd12_20130611_015335"

