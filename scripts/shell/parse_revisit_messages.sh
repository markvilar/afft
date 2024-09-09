#!/usr/bin/bash

DEVICE="/home/martin/data"
MESSAGE_DIR="$DEVICE/acfr_revisits_messages/acfr_merged_messages"
OUTPUT_DIR="$DEVICE/acfr_revisits_messages/acfr_parsed_messages"

poetry run afft-cli parse-messages \
  "$MESSAGE_DIR/qd61g27j_20100421_022145_messages.txt" \
  "$OUTPUT_DIR/qd61g27j_20100421_022145_messages.hdf5" \
  "$CONFIG_DIR/protocol/protocol_v1.toml"

exit 0

poetry run afft-cli parse-messages "$MESSAGE_DIR/qd61g27j_20110410_011202_messages.txt" <protocol>
poetry run afft-cli parse-messages "$MESSAGE_DIR/qd61g27j_20120422_043114_messages.txt" <protocol>
poetry run afft-cli parse-messages "$MESSAGE_DIR/qd61g27j_20130414_013620_messages.txt" <protocol>
poetry run afft-cli parse-messages "$MESSAGE_DIR/qd61g27j_20170523_040815_messages.txt" <protocol>

