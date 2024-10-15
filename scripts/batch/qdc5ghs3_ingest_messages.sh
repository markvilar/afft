#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdc5ghs3_20100430_024508_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdc5ghs3_20100430_024508"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdc5ghs3_20120501_033336_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdc5ghs3_20120501_033336"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdc5ghs3_20130405_103429_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdc5ghs3_20130405_103429"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdc5ghs3_20210315_230947_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdc5ghs3_20210315_230947"

