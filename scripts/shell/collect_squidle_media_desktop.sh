#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DESCRIPTOR_FILE="${REPO_ROOT}/data/deployment_descriptors_v1_all_enriched.toml"
OUTPUT_DIR="/data/exos_01/acfr_squidle_collections"


echo "Script dir: ${SCRIPT_DIR}"
echo "Descriptor file: ${DESCRIPTOR_FILE}"


uv run afft tasks collect-squidle-media \
  --deployments-file "${DESCRIPTOR_FILE}" \
  --output-dir "${OUTPUT_DIR}"
