#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20100428_020202_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20100428_020202"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20110415_020103_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20110415_020103"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20120430_002423_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20120430_002423"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20130406_023610_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20130406_023610"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20140327_071251_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20140327_071251"
 
poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20170526_025746_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20170526_025746"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qdch0ftq_20210315_034028_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qdch0ftq_20210315_034028"
