#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(realpath -m ${SCRIPT_DIR}/../../config)"

OUTPUT_DIR="${HOME}/data/acfr_squidle_collections"


echo "Script dir: ${SCRIPT_DIR}"
echo "Config dir: ${CONFIG_DIR}"


uv run afft tasks collect-squidle-media \
  --deployments-file "${CONFIG_DIR}/acfr_deployments.toml" \
  --output-dir "${OUTPUT_DIR}"
