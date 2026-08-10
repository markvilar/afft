#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DEPLOYMENT_BUNDLE_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset"
SEALEVEL_DATA_DIR="/data/exos_01/metocean_sea_level_hourly"

FRAME_KEY="metocean/worldtides/sealevel"
DATETIME_COLUMN="datetime"

# Bundle file to sea level file. The sea level series are per site rather
# than per deployment, so the deployments sharing a site share a file.
declare -A INGESTIONS=(
  ["qdch0ftq_20100428_020202_deployment_bundle.sqlite"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20110415_020103_deployment_bundle.sqlite"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20120430_002423_deployment_bundle.sqlite"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdch0ftq_20130406_023610_deployment_bundle.sqlite"]="qdch0ftq_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20110416_005411_deployment_bundle.sqlite"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20120501_071203_deployment_bundle.sqlite"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20130406_081713_deployment_bundle.sqlite"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["qdchdmy1_20170525_234624_deployment_bundle.sqlite"]="qdchdmy1_20090101_20211231_sea_level.csv"
  ["r23685bc_20100605_021022_deployment_bundle.sqlite"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r23685bc_20120530_233021_deployment_bundle.sqlite"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r23685bc_20140616_225022_deployment_bundle.sqlite"]="r23685bc_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20090612_225306_deployment_bundle.sqlite"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20110612_033752_deployment_bundle.sqlite"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r29mrd5h_20130611_002419_deployment_bundle.sqlite"]="r29mrd5h_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20101023_210332_deployment_bundle.sqlite"]="r7jjskxq_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20121013_060425_deployment_bundle.sqlite"]="r7jjskxq_20090101_20211231_sea_level.csv"
  ["r7jjskxq_20131022_004934_deployment_bundle.sqlite"]="r7jjskxq_20090101_20211231_sea_level.csv"
)

# Associative arrays iterate in hash order, so sort the keys to keep runs
# reproducible and their logs comparable.
for bundle_file in $(printf "%s\n" "${!INGESTIONS[@]}" | sort); do
  # Retrieve sealevel file from associative array
  sealevel_file="${INGESTIONS[${bundle_file}]}"

  bundle_path="${DEPLOYMENT_BUNDLE_DIR}/${bundle_file}"
  sealevel_path="${SEALEVEL_DATA_DIR}/${sealevel_file}"

  uv run afft bundle ingest-frame \
    --bundle "${bundle_path}" \
    --key "${FRAME_KEY}" \
    --file "${sealevel_path}" \
    --datetime-column "${DATETIME_COLUMN}" \
    --overwrite
done
