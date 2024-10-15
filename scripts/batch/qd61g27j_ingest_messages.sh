#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qd61g27j_20100421_022145_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qd61g27j_20100421_022145"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qd61g27j_20110410_011202_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qd61g27j_20110410_011202"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qd61g27j_20120422_043114_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qd61g27j_20120422_043114"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qd61g27j_20130414_013620_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qd61g27j_20130414_013620"

poetry run afft parse-messages \
  "${MESSAGE_DIR}/qd61g27j_20170523_040815_messages.txt" \
  "${CONFIG}" \
  --database "acfr_auv_messages" \
  --host "localhost" \
  --port 5432 \
  --prefix "qd61g27j_20170523_040815"



