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
PRIOR_CAMERA_POSE_DATA_DIR="/data/exos_01/acfr_stereo_camera_poses_v1_renav_squidle_merged"
REGISTERED_CAMERA_POSE_DATA_DIR="/data/exos_01/acfr_stereo_camera_poses_v1_benthloc_registered"
OUTPUT_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset"

SEALEVEL_KEY="metocean/worldtides/sealevel"
PRIOR_CAMERA_POSE_KEY="trajectory/renav_priors/stereo_camera_poses"
REGISTERED_CAMERA_POSE_KEY="trajectory/metashape_registered/stereo_camera_poses"

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

# Prior (renav/squidle-merged) camera pose file per deployment.
declare -A PRIOR_CAMERA_POSE_FILES=(
  ["qdch0ftq_20100428_020202"]="qdch0ftq_20100428_020202_stereo_camera_poses_renav.geojson"
  ["qdch0ftq_20110415_020103"]="qdch0ftq_20110415_020103_stereo_camera_poses_renav.geojson"
  ["qdch0ftq_20120430_002423"]="qdch0ftq_20120430_002423_stereo_camera_poses_renav.geojson"
  ["qdch0ftq_20130406_023610"]="qdch0ftq_20130406_023610_stereo_camera_poses_renav.geojson"
  ["qdchdmy1_20110416_005411"]="qdchdmy1_20110416_005411_stereo_camera_poses_renav.geojson"
  ["qdchdmy1_20120501_071203"]="qdchdmy1_20120501_071203_stereo_camera_poses_renav.geojson"
  ["qdchdmy1_20130406_081713"]="qdchdmy1_20130406_081713_stereo_camera_poses_renav.geojson"
  ["qdchdmy1_20170525_234624"]="qdchdmy1_20170525_234624_stereo_camera_poses_renav.geojson"
  ["r23685bc_20100605_021022"]="r23685bc_20100605_021022_stereo_camera_poses_renav.geojson"
  ["r23685bc_20120530_233021"]="r23685bc_20120530_233021_stereo_camera_poses_renav.geojson"
  ["r23685bc_20140616_225022"]="r23685bc_20140616_225022_stereo_camera_poses_renav.geojson"
  ["r29mrd5h_20090612_225306"]="r29mrd5h_20090612_225306_stereo_camera_poses_renav.geojson"
  ["r29mrd5h_20110612_033752"]="r29mrd5h_20110612_033752_stereo_camera_poses_renav.geojson"
  ["r29mrd5h_20130611_002419"]="r29mrd5h_20130611_002419_stereo_camera_poses_renav.geojson"
  ["r7jjskxq_20101023_210332"]="r7jjskxq_20101023_210332_stereo_camera_poses_renav.geojson"
  ["r7jjskxq_20121013_060425"]="r7jjskxq_20121013_060425_stereo_camera_poses_renav.geojson"
  ["r7jjskxq_20131022_004934"]="r7jjskxq_20131022_004934_stereo_camera_poses_renav.geojson"
)

# Registered (benthloc-registered) stereo camera pose file per deployment.
declare -A REGISTERED_CAMERA_POSE_FILES=(
  ["qdch0ftq_20100428_020202"]="qdch0ftq_20100428_020202_stereo_camera_poses.geojson"
  ["qdch0ftq_20110415_020103"]="qdch0ftq_20110415_020103_stereo_camera_poses.geojson"
  ["qdch0ftq_20120430_002423"]="qdch0ftq_20120430_002423_stereo_camera_poses.geojson"
  ["qdch0ftq_20130406_023610"]="qdch0ftq_20130406_023610_stereo_camera_poses.geojson"
  ["qdchdmy1_20110416_005411"]="qdchdmy1_20110416_005411_stereo_camera_poses.geojson"
  ["qdchdmy1_20120501_071203"]="qdchdmy1_20120501_071203_stereo_camera_poses.geojson"
  ["qdchdmy1_20130406_081713"]="qdchdmy1_20130406_081713_stereo_camera_poses.geojson"
  ["qdchdmy1_20170525_234624"]="qdchdmy1_20170525_234624_stereo_camera_poses.geojson"
  ["r23685bc_20100605_021022"]="r23685bc_20100605_021022_stereo_camera_poses.geojson"
  ["r23685bc_20120530_233021"]="r23685bc_20120530_233021_stereo_camera_poses.geojson"
  ["r23685bc_20140616_225022"]="r23685bc_20140616_225022_stereo_camera_poses.geojson"
  ["r29mrd5h_20090612_225306"]="r29mrd5h_20090612_225306_stereo_camera_poses.geojson"
  ["r29mrd5h_20110612_033752"]="r29mrd5h_20110612_033752_stereo_camera_poses.geojson"
  ["r29mrd5h_20130611_002419"]="r29mrd5h_20130611_002419_stereo_camera_poses.geojson"
  ["r7jjskxq_20101023_210332"]="r7jjskxq_20101023_210332_stereo_camera_poses.geojson"
  ["r7jjskxq_20121013_060425"]="r7jjskxq_20121013_060425_stereo_camera_poses.geojson"
  ["r7jjskxq_20131022_004934"]="r7jjskxq_20131022_004934_stereo_camera_poses.geojson"
)

# Building overwrites the bundle, so the sea level ingestion has to follow the
# build of the same deployment rather than run as a second pass over all of
# them -- a rebuild would otherwise discard a frame ingested earlier.
#
# Associative arrays iterate in hash order, so sort the keys to keep runs
# reproducible and their logs comparable.
for deployment in $(printf "%s\n" "${!SEALEVEL_FILES[@]}" | sort); do
  bundle_file="${OUTPUT_DIR}/${deployment}_deployment_bundle.gpkg"
  sealevel_file="${SEALEVEL_DATA_DIR}/${SEALEVEL_FILES[${deployment}]}"
  prior_camera_pose_file="${PRIOR_CAMERA_POSE_DATA_DIR}/${PRIOR_CAMERA_POSE_FILES[${deployment}]}"
  registered_camera_pose_file="${REGISTERED_CAMERA_POSE_DATA_DIR}/${REGISTERED_CAMERA_POSE_FILES[${deployment}]}"

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
    --datetime-column "timestamp" \
    --overwrite

  uv run afft bundle ingest-frame \
    --bundle "${bundle_file}" \
    --key "${PRIOR_CAMERA_POSE_KEY}" \
    --file "${prior_camera_pose_file}" \
    --datetime-column "timestamp" \
    --overwrite

  uv run afft bundle ingest-frame \
    --bundle "${bundle_file}" \
    --key "${REGISTERED_CAMERA_POSE_KEY}" \
    --file "${registered_camera_pose_file}" \
    --datetime-column "timestamp" \
    --overwrite
done
