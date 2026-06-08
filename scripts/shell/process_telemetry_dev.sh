#!/usr/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

CONFIG_DIR="${SCRIPT_DIR}/../../config"
SOURCE_DIR="/data/exos_01/acfr_messages_v3_metocean_corrected"
OUTPUT_DIR="/data/exos_01/acfr_messages_v4_telemetry_processed"

echo "Config directory: ${CONFIG_DIR}"
echo "Source directory: ${SOURCE_DIR}"

# --------------------------------------------------------------------------------------
# Telemetry Processing - Site 1 - QDCH0FTQ
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_dev.toml" \
  --pattern "qdch0ftq_20100428_020202_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_dev.toml" \
  --pattern "qdch0ftq_20110415_020103_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_dev.toml" \
  --pattern "qdch0ftq_20120430_002423_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_dev.toml" \
  --pattern "qdch0ftq_20130406_023610_*"

# --------------------------------------------------------------------------------------
# Telemetry Processing - Site 2 - QDCHDMY1
# --------------------------------------------------------------------------------------

# TODO: Add telmetry processing commands

# --------------------------------------------------------------------------------------
# Telemetry Processing - Site 3 - R23685BC
# --------------------------------------------------------------------------------------

# TODO: Add telmetry processing commands

# --------------------------------------------------------------------------------------
# Telemetry Processing - Site 4 - R29MRD5H
# --------------------------------------------------------------------------------------

# TODO: Add telmetry processing commands

# --------------------------------------------------------------------------------------
# Telemetry Processing - Site 5 - R7JJSKXQ
# --------------------------------------------------------------------------------------
