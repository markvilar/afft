#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DESCRIPTOR_FILE="${REPO_ROOT}/data/deployment_descriptors_v1_subset_enriched.toml"
CONFIG_FILE="${REPO_ROOT}/config/default.toml"

DEPLOYMENT_DATA_DIR="${HOME}/data/acfr_deployments_v1_subset_fixed"
SEALEVEL_DATA_DIR="${HOME}/data/metocean_sea_level_hourly"
RENAV_PRIOR_TRAJECTORY_DATA_DIR="${HOME}/data/acfr_sirius_poses_v1_renav_priors"
OUTPUT_DIR="${HOME}/data/acfr_deployment_bundles_v1_subset"

SEALEVEL_KEY="metocean/worldtides/sealevel"
SEALEVEL_DATETIME_COLUMN="timestamp"

RENAV_PRIOR_TRAJECTORY_KEY="trajectory/renav_prior/platform_poses"
RENAV_PRIOR_TRAJECTORY_DATETIME_COLUMN="timestamp"

# Sea level file per deployment. The series are per site rather than per
# deployment, so the deployments sharing a site share a file.
declare -A SEALEVEL_FILES=(
  ["qdch0ftq_20100428_020202"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20110415_020103"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20120430_002423"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20130406_023610"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20110416_005411"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20120501_071203"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20130406_081713"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20170525_234624"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["r23685bc_20100605_021022"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r23685bc_20120530_233021"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r23685bc_20140616_225022"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20090612_225306"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20110612_033752"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20130611_002419"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20101023_210332"]="r7jjskxq_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20121013_060425"]="r7jjskxq_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20131022_004934"]="r7jjskxq_20090101_20211231_sea_level.csv"
)

# Renav prior trajectory file per deployment.
declare -A RENAV_PRIOR_TRAJECTORY_FILES=(
  ["qdch0ftq_20100428_020202"]="qdch0ftq_20100428_020202_platform_poses.csv"
  ["qdch0ftq_20110415_020103"]="qdch0ftq_20110415_020103_platform_poses.csv"
  ["qdch0ftq_20120430_002423"]="qdch0ftq_20120430_002423_platform_poses.csv"
  ["qdch0ftq_20130406_023610"]="qdch0ftq_20130406_023610_platform_poses.csv"
  ["qdchdmy1_20110416_005411"]="qdchdmy1_20110416_005411_platform_poses.csv"
  ["qdchdmy1_20120501_071203"]="qdchdmy1_20120501_071203_platform_poses.csv"
  ["qdchdmy1_20130406_081713"]="qdchdmy1_20130406_081713_platform_poses.csv"
  ["qdchdmy1_20170525_234624"]="qdchdmy1_20170525_234624_platform_poses.csv"
  ["r23685bc_20100605_021022"]="r23685bc_20100605_021022_platform_poses.csv"
  ["r23685bc_20120530_233021"]="r23685bc_20120530_233021_platform_poses.csv"
  ["r23685bc_20140616_225022"]="r23685bc_20140616_225022_platform_poses.csv"
  ["r29mrd5h_20090612_225306"]="r29mrd5h_20090612_225306_platform_poses.csv"
  ["r29mrd5h_20110612_033752"]="r29mrd5h_20110612_033752_platform_poses.csv"
  ["r29mrd5h_20130611_002419"]="r29mrd5h_20130611_002419_platform_poses.csv"
  ["r7jjskxq_20101023_210332"]="r7jjskxq_20101023_210332_platform_poses.csv"
  ["r7jjskxq_20121013_060425"]="r7jjskxq_20121013_060425_platform_poses.csv"
  ["r7jjskxq_20131022_004934"]="r7jjskxq_20131022_004934_platform_poses.csv"
)

# Building overwrites the bundle, so the sea level ingestion has to follow the
# build of the same deployment rather than run as a second pass over all of
# them -- a rebuild would otherwise discard a frame ingested earlier.
#
# Associative arrays iterate in hash order, so sort the keys to keep runs
# reproducible and their logs comparable.
for deployment in $(printf "%s\n" "${!SEALEVEL_FILES[@]}" | sort); do
  bundle_file="${OUTPUT_DIR}/${deployment}_deployment_bundle.sqlite"
  sealevel_file="${SEALEVEL_DATA_DIR}/${SEALEVEL_FILES[${deployment}]}"
  renav_prior_trajectory_file="${RENAV_PRIOR_TRAJECTORY_DATA_DIR}/${RENAV_PRIOR_TRAJECTORY_FILES[${deployment}]}"

  uv run afft bundle build \
    --descriptor-file "${DESCRIPTOR_FILE}" \
    --data-dir "${DEPLOYMENT_DATA_DIR}/${deployment}_deployment_data" \
    --config "${CONFIG_FILE}" \
    --deployment-label "${deployment}" \
    --output "${bundle_file}" \
    --overwrite

  uv run afft bundle ingest-frame \
    --bundle "${bundle_file}" \
    --key "${SEALEVEL_KEY}" \
    --file "${sealevel_file}" \
    --datetime-column "${SEALEVEL_DATETIME_COLUMN}" \
    --overwrite

  uv run afft bundle ingest-frame \
    --bundle "${bundle_file}" \
    --key "${RENAV_PRIOR_TRAJECTORY_KEY}" \
    --file "${renav_prior_trajectory_file}" \
    --datetime-column "${RENAV_PRIOR_TRAJECTORY_DATETIME_COLUMN}" \
    --overwrite
done
