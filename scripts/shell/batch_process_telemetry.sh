#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../../config"

SOURCE_DIR="/data/exos_01/acfr_messages_v3_metocean_corrected"
OUTPUT_DIR="/data/exos_01/acfr_messages_v4_processed"

# --------------------------------------------------------------------------------------
# Site 1 - QDCH0FTQ
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdch0ftq_20100428_020202_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdch0ftq_20110415_020103_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdch0ftq_20120430_002423_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdch0ftq_20130406_023610_*"

# --------------------------------------------------------------------------------------
# Site 2 - QDCHDMY1
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdchdmy1_20110416_005411_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdchdmy1_20120501_071203_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdchdmy1_20130406_081713_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "qdchdmy1_20170525_234624_*"

# --------------------------------------------------------------------------------------
# Site 3 - R23685BC
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r23685bc_20100605_021022_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r23685bc_20120530_233021_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r23685bc_20140616_225022_*"

# --------------------------------------------------------------------------------------
# Site 4 - R29MRD5H
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r29mrd5h_20090612_225306_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r29mrd5h_20110612_033752_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r29mrd5h_20130611_002419_*"

# --------------------------------------------------------------------------------------
# Site 5 - R7JJSKXQ
# --------------------------------------------------------------------------------------

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r7jjskxq_20101023_210332_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r7jjskxq_20121013_060425_*"

uv run afft tasks process-telemetry "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --config "${CONFIG_DIR}/telemetry_config_default.toml" \
  --pattern "r7jjskxq_20131022_004934_*"
