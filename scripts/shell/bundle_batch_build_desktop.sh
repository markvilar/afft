#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DESCRIPTOR_FILE="${REPO_ROOT}/data/deployment_descriptors_v1_subset_enriched.toml"
CONFIG_FILE="${REPO_ROOT}/config/default.toml"

DEPLOYMENT_DATA_DIR="/data/exos_01/acfr_deployments_v1_subset_fixed"
SEALEVEL_DATA_DIR="/data/exos_01/metocean_sea_level_hourly"
OUTPUT_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset"

DEPLOYMENTS=(
  "qdch0ftq_20100428_020202"
  "qdch0ftq_20110415_020103"
  "qdch0ftq_20120430_002423"
  "qdch0ftq_20130406_023610"
  "qdchdmy1_20110416_005411"
  "qdchdmy1_20120501_071203"
  "qdchdmy1_20130406_081713"
  "qdchdmy1_20170525_234624"
  "r23685bc_20100605_021022"
  "r23685bc_20120530_233021"
  "r23685bc_20140616_225022"
  "r29mrd5h_20090612_225306"
  "r29mrd5h_20110612_033752"
  "r29mrd5h_20130611_002419"
  "r7jjskxq_20101023_210332"
  "r7jjskxq_20121013_060425"
  "r7jjskxq_20131022_004934"
)

for deployment in "${DEPLOYMENTS[@]}"; do
  uv run afft bundle build \
    --descriptor-file "${DESCRIPTOR_FILE}" \
    --data-dir "${DEPLOYMENT_DATA_DIR}/${deployment}_deployment_data" \
    --config "${CONFIG_FILE}" \
    --deployment-label "${deployment}" \
    --output "${OUTPUT_DIR}/${deployment}_deployment_bundle.sqlite" \
    --overwrite
done
