#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BUNDLE_DATA_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset_processed"
OUTPUT_DIR="/data/exos_01/acfr_benthloc_ingestion/acfr_benthloc_telemetry_ingestion_v1"

LINKQUEST_CONFIG="${REPO_ROOT}/config/telemetry_ingestion_linkquest.toml"
EVOLOGICS_CONFIG="${REPO_ROOT}/config/telemetry_ingestion_evologics.toml"

# Deployment bundle file per deployment.
declare -A BUNDLE_FILES=(
  ["qdch0ftq_20100428_020202"]="qdch0ftq_20100428_020202_deployment_bundle.gpkg"
  ["qdch0ftq_20110415_020103"]="qdch0ftq_20110415_020103_deployment_bundle.gpkg"
  ["qdch0ftq_20120430_002423"]="qdch0ftq_20120430_002423_deployment_bundle.gpkg"
  ["qdch0ftq_20130406_023610"]="qdch0ftq_20130406_023610_deployment_bundle.gpkg"
  ["qdchdmy1_20110416_005411"]="qdchdmy1_20110416_005411_deployment_bundle.gpkg"
  ["qdchdmy1_20120501_071203"]="qdchdmy1_20120501_071203_deployment_bundle.gpkg"
  ["qdchdmy1_20130406_081713"]="qdchdmy1_20130406_081713_deployment_bundle.gpkg"
  ["qdchdmy1_20170525_234624"]="qdchdmy1_20170525_234624_deployment_bundle.gpkg"
  ["r23685bc_20100605_021022"]="r23685bc_20100605_021022_deployment_bundle.gpkg"
  ["r23685bc_20120530_233021"]="r23685bc_20120530_233021_deployment_bundle.gpkg"
  ["r23685bc_20140616_225022"]="r23685bc_20140616_225022_deployment_bundle.gpkg"
  ["r29mrd5h_20090612_225306"]="r29mrd5h_20090612_225306_deployment_bundle.gpkg"
  ["r29mrd5h_20110612_033752"]="r29mrd5h_20110612_033752_deployment_bundle.gpkg"
  ["r29mrd5h_20130611_002419"]="r29mrd5h_20130611_002419_deployment_bundle.gpkg"
  ["r7jjskxq_20101023_210332"]="r7jjskxq_20101023_210332_deployment_bundle.gpkg"
  ["r7jjskxq_20121013_060425"]="r7jjskxq_20121013_060425_deployment_bundle.gpkg"
  ["r7jjskxq_20131022_004934"]="r7jjskxq_20131022_004934_deployment_bundle.gpkg"
)

# Telemetry ingestion config per deployment. The USBL family sets the config:
# deployments before 2015 carry the LinkQuest USBL, deployments from 2015 on
# carry the EvoLogics USBL. Only qdchdmy1_20170525_234624 is EvoLogics in this
# subset.
declare -A CONFIG_FILES=(
  ["qdch0ftq_20100428_020202"]="${LINKQUEST_CONFIG}"
  ["qdch0ftq_20110415_020103"]="${LINKQUEST_CONFIG}"
  ["qdch0ftq_20120430_002423"]="${LINKQUEST_CONFIG}"
  ["qdch0ftq_20130406_023610"]="${LINKQUEST_CONFIG}"
  ["qdchdmy1_20110416_005411"]="${LINKQUEST_CONFIG}"
  ["qdchdmy1_20120501_071203"]="${LINKQUEST_CONFIG}"
  ["qdchdmy1_20130406_081713"]="${LINKQUEST_CONFIG}"
  ["qdchdmy1_20170525_234624"]="${EVOLOGICS_CONFIG}"
  ["r23685bc_20100605_021022"]="${LINKQUEST_CONFIG}"
  ["r23685bc_20120530_233021"]="${LINKQUEST_CONFIG}"
  ["r23685bc_20140616_225022"]="${LINKQUEST_CONFIG}"
  ["r29mrd5h_20090612_225306"]="${LINKQUEST_CONFIG}"
  ["r29mrd5h_20110612_033752"]="${LINKQUEST_CONFIG}"
  ["r29mrd5h_20130611_002419"]="${LINKQUEST_CONFIG}"
  ["r7jjskxq_20101023_210332"]="${LINKQUEST_CONFIG}"
  ["r7jjskxq_20121013_060425"]="${LINKQUEST_CONFIG}"
  ["r7jjskxq_20131022_004934"]="${LINKQUEST_CONFIG}"
)

mkdir -p "${OUTPUT_DIR}"

# Associative arrays iterate in hash order, so sort the keys to keep runs
# reproducible and their logs comparable.
for deployment in $(printf "%s\n" "${!BUNDLE_FILES[@]}" | sort); do
  bundle_file="${BUNDLE_DATA_DIR}/${BUNDLE_FILES[${deployment}]}"
  config_file="${CONFIG_FILES[${deployment}]}"
  output_file="${OUTPUT_DIR}/${deployment}_deployment_telemetry_v1.json"

  uv run afft benthloc build-telemetry-ingestion-document \
    --bundle "${bundle_file}" \
    --config "${config_file}" \
    --output "${output_file}" \
    --overwrite \
    --verbose
done
