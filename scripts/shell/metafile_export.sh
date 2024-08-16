#!/usr/bin/bash

DATA_DIR="/home/martin/data/acfr_revisits_unprocessed/acfr_measurements_unprocessed"
METAFILE_DIR="/home/martin/data/acfr_revisits_processed/acfr_metafiles"
OUTPUT_DIR="/home/martin/data/acfr_revisits_processed/acfr_rawfile_export"

poetry run raft-cli metafile-export "$DATA_DIR/qd61g27j" "$METAFILE_DIR/qd61g27j_metafile.toml" \
  "$OUTPUT_DIR" --prefix "qd61g27j"

poetry run raft-cli metafile-export "$DATA_DIR/qdc5ghs3" "$METAFILE_DIR/qdc5ghs3_metafile.toml" \
  "$OUTPUT_DIR" --prefix "qdc5ghs3"
poetry run raft-cli metafile-export "$DATA_DIR/qdch0ftq" "$METAFILE_DIR/qdch0ftq_metafile.toml" \
  "$OUTPUT_DIR" --prefix "qdch0ftq"
poetry run raft-cli metafile-export "$DATA_DIR/qdchdmy1" "$METAFILE_DIR/qdchdmy1_metafile.toml" \
  "$OUTPUT_DIR" --prefix "qdchdmy1"
poetry run raft-cli metafile-export "$DATA_DIR/qtqxshxs" "$METAFILE_DIR/qtqxshxs_metafile.toml" \
  "$OUTPUT_DIR" --prefix "qtqxshxs"
poetry run raft-cli metafile-export "$DATA_DIR/r7jjskxq" "$METAFILE_DIR/r7jjskxq_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r7jjskxq"
poetry run raft-cli metafile-export "$DATA_DIR/r7jjss8n" "$METAFILE_DIR/r7jjss8n_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r7jjss8n"
poetry run raft-cli metafile-export "$DATA_DIR/r7jjssbh" "$METAFILE_DIR/r7jjssbh_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r7jjssbh"
poetry run raft-cli metafile-export "$DATA_DIR/r23m7ms0" "$METAFILE_DIR/r23m7ms0_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r23m7ms0"
poetry run raft-cli metafile-export "$DATA_DIR/r29mrd5h" "$METAFILE_DIR/r29mrd5h_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r29mrd5h"
poetry run raft-cli metafile-export "$DATA_DIR/r29mrd12" "$METAFILE_DIR/r29mrd12_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r29mrd12"
poetry run raft-cli metafile-export "$DATA_DIR/r234xgje" "$METAFILE_DIR/r234xgje_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r234xgje"
poetry run raft-cli metafile-export "$DATA_DIR/r23685bc" "$METAFILE_DIR/r23685bc_metafile.toml" \
  "$OUTPUT_DIR" --prefix "r23685bc"
