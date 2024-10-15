#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20110416_005411_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20110416_005411"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20120501_071203_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20120501_071203"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20130406_081713_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20130406_081713"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20140328_063358_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20140328_063358"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20170525_234624_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20170525_234624"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdchdmy1_20210315_081519_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdchdmy1_20210315_081519"
