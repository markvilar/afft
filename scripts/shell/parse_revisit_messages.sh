#!/usr/bin/bash

MESSAGE_DIR="/home/martin/data/acfr_revisits_messages/acfr_merged_messages"

poetry run afft parse-messages "${MESSAGE_DIR}/r23685bc_20100605_021022_messages.txt" \
  "./config/protocol/protocol_v1.toml"

exit 0

poetry run afft parse-messages "$MESSAGE_DIR/qd61g27j_20110410_011202_messages.txt" <protocol>
poetry run afft parse-messages "$MESSAGE_DIR/qd61g27j_20120422_043114_messages.txt" <protocol>
poetry run afft parse-messages "$MESSAGE_DIR/qd61g27j_20130414_013620_messages.txt" <protocol>
poetry run afft parse-messages "$MESSAGE_DIR/qd61g27j_20170523_040815_messages.txt" <protocol>

