#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CONFIG_FILE="${REPO_ROOT}/config/default.toml"

INPUT_DIR="${HOME}/data/acfr_deployment_bundles_v1_subset"
OUTPUT_DIR="${HOME}/data/acfr_deployment_bundles_v1_subset_processed"

BUNDLE_FILES=(
  "qdch0ftq_20100428_020202_deployment_bundle.gpkg"
  "qdch0ftq_20110415_020103_deployment_bundle.gpkg"
  "qdch0ftq_20120430_002423_deployment_bundle.gpkg"
  "qdch0ftq_20130406_023610_deployment_bundle.gpkg"
  "qdchdmy1_20110416_005411_deployment_bundle.gpkg"
  "qdchdmy1_20120501_071203_deployment_bundle.gpkg"
  "qdchdmy1_20130406_081713_deployment_bundle.gpkg"
  "qdchdmy1_20170525_234624_deployment_bundle.gpkg"
  "r23685bc_20100605_021022_deployment_bundle.gpkg"
  "r23685bc_20120530_233021_deployment_bundle.gpkg"
  "r23685bc_20140616_225022_deployment_bundle.gpkg"
  "r29mrd5h_20090612_225306_deployment_bundle.gpkg"
  "r29mrd5h_20110612_033752_deployment_bundle.gpkg"
  "r29mrd5h_20130611_002419_deployment_bundle.gpkg"
  "r7jjskxq_20101023_210332_deployment_bundle.gpkg"
  "r7jjskxq_20121013_060425_deployment_bundle.gpkg"
  "r7jjskxq_20131022_004934_deployment_bundle.gpkg"
)

mkdir -p "${OUTPUT_DIR}"

for bundle_file in "${BUNDLE_FILES[@]}"; do
  uv run afft bundle process \
    --input "${INPUT_DIR}/${bundle_file}" \
    --output "${OUTPUT_DIR}/${bundle_file}" \
    --config "${CONFIG_FILE}" \
    --overwrite \
    --verbose
done
