#!/usr/bin/bash

DATA_DIRECTORY="/home/martin/data/acfr_revisits_unprocessed/acfr_measurements_unprocessed"
OUTPUT_DIRECTORY="/home/martin/data/acfr_revisits_processed/acfr_metafiles"

CONFIG_FILE="config/tasks/metafile_generation.toml"

poetry run afft-cli generate "$DATA_DIRECTORY/qd61g27j" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "qd61g27j"
poetry run afft-cli generate "$DATA_DIRECTORY/qdc5ghs3" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "qdc5ghs3"
poetry run afft-cli generate "$DATA_DIRECTORY/qdch0ftq" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "qdch0ftq"
poetry run afft-cli generate "$DATA_DIRECTORY/qdchdmy1" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "qdchdmy1"
poetry run afft-cli generate "$DATA_DIRECTORY/qtqxshxs" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "qtqxshxs"
poetry run afft-cli generate "$DATA_DIRECTORY/r7jjskxq" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r7jjskxq"
poetry run afft-cli generate "$DATA_DIRECTORY/r7jjss8n" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r7jjss8n"
poetry run afft-cli generate "$DATA_DIRECTORY/r7jjssbh" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r7jjssbh"
poetry run afft-cli generate "$DATA_DIRECTORY/r23m7ms0" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r23m7ms0"
poetry run afft-cli generate "$DATA_DIRECTORY/r29mrd5h" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r29mrd5h"
poetry run afft-cli generate "$DATA_DIRECTORY/r29mrd12" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r29mrd12"
poetry run afft-cli generate "$DATA_DIRECTORY/r234xgje" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r234xgje"
poetry run afft-cli generate "$DATA_DIRECTORY/r23685bc" "$OUTPUT_DIRECTORY" "$CONFIG_FILE" \
  --prefix "r23685bc"

exit 0
