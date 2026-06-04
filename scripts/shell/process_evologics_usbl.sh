#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../../config"

SOURCE_DIR="/data/exos_01/acfr_messages_v2_parsed"
OUTPUT_DIR="/data/exos_01/acfr_messages_v4_telemetry_processed"

# --------------------------------------------------------------------------------------
# Site 1
# --------------------------------------------------------------------------------------

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20170526_025746_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20170526_025746_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20170526_025746"

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20210315_034028_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20210315_034028_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20210315_034028"

# --------------------------------------------------------------------------------------
# Site 2
# --------------------------------------------------------------------------------------

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20170525_234624_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20170525_234624_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20170525_234624"

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20210315_081519_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20210315_081519_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20210315_081519"

# --------------------------------------------------------------------------------------
# Site 3
# --------------------------------------------------------------------------------------

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qd61g27j_20170523_040815_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qd61g27j_20170523_040815_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qd61g27j_20170523_040815"

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qdc5ghs3_20210315_230947_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qdc5ghs3_20210315_230947_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qdc5ghs3_20210315_230947"

# --------------------------------------------------------------------------------------
# Site 4 (Tasmania Bluefin)
# --------------------------------------------------------------------------------------

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qtqxshxs_20150327_015552_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qtqxshxs_20150327_015552_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qtqxshxs_20150327_015552"

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qtqxshxs_20150328_000850_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qtqxshxs_20150328_000850_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qtqxshxs_20150328_000850"

uv run afft sensors process-evologics-usbl \
  --usbl-file "${SOURCE_DIR}/qtqxshxs_20150328_042551_usbl_evologics.csv" \
  --output-file "${OUTPUT_DIR}/qtqxshxs_20150328_042551_usbl_evologics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qtqxshxs_20150328_042551"
