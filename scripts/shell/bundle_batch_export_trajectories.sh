#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

INPUT_DIR="${HOME}/data/acfr_deployment_bundles_v1_subset_processed"
OUTPUT_DIR="${HOME}/data/acfr_benthloc_ingestion/acfr_benthloc_trajectory_ingestion_v1"

# Fields: bundle key|trajectory label
TRAJECTORY_SOURCES=(
  "trajectory/renav_priors/platform_poses|renav_prior"
  "trajectory/metashape_registered/platform_poses|metashape_registered"
)

mkdir -p "${OUTPUT_DIR}"

cd "${REPO_ROOT}"

for bundle_file in "${INPUT_DIR}"/*_deployment_bundle.gpkg; do
  deployment_label="$(basename "${bundle_file}" _deployment_bundle.gpkg)"

  for source in "${TRAJECTORY_SOURCES[@]}"; do
    IFS="|" read -r key trajectory_label <<< "${source}"

    output_file="${OUTPUT_DIR}/${deployment_label}_${trajectory_label}_trajectory_ingestion.geojson"

    uv run afft benthloc build-trajectory-ingestion-file \
      --bundle "${bundle_file}" \
      --key "${key}" \
      --output "${output_file}" \
      --trajectory-label "${trajectory_label}" \
      --overwrite
  done
done
