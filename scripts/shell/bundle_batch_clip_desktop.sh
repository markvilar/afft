#!/usr/bin/bash

# Exit on the first failing command, on any unset variable, and on a failure
# anywhere in a pipeline rather than only in its last command.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

INPUT_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset"
OUTPUT_DIR="/data/exos_01/acfr_deployment_bundles_v1_subset_dense_grids"

# Appended to each source deployment label to name the clipped deployment.
# One dense grid is cut per full-grid deployment, so the suffix is the same
# for every row; a second segment from the same parent would need its own.
LABEL_SUFFIX="dense01"

# Metocean series are sampled far coarser than telemetry -- often hourly --
# so a dense-grid window would clip a forcing series to one row or none.
# Metocean describes conditions rather than the vehicle's track, so the
# dense-grid bundle keeps the full series.
NO_CLIP_PATTERN="metocean/*"

# Dense-grid temporal ranges, one row per deployment, as recorded in #266.
# Each range is a subset of the full-grid deployment carrying the same label,
# bracketed 10 seconds around the first and last dense-grid image.
#
# The clip window is closed, so both bounds are kept and the ranges transfer
# exactly as #266 states them.
#
# Fields: deployment_label|start_time|end_time
DENSE_GRID_RANGES=(
  "qdch0ftq_20100428_020202|2010-04-28T03:54:39Z|2010-04-28T04:33:41Z"
  "qdch0ftq_20110415_020103|2011-04-15T03:42:40Z|2011-04-15T04:20:34Z"
  "qdch0ftq_20120430_002423|2012-04-30T02:07:21Z|2012-04-30T02:44:19Z"
  "qdch0ftq_20130406_023610|2013-04-06T05:03:44Z|2013-04-06T05:39:38Z"
  "qdchdmy1_20110416_005411|2011-04-16T00:58:13Z|2011-04-16T01:37:09Z"
  "qdchdmy1_20120501_071203|2012-05-01T07:15:14Z|2012-05-01T07:52:50Z"
  "qdchdmy1_20130406_081713|2013-04-06T08:24:09Z|2013-04-06T09:00:32Z"
  "qdchdmy1_20170525_234624|2017-05-25T23:59:45Z|2017-05-26T00:38:37Z"
  "r23685bc_20100605_021022|2010-06-05T03:00:40Z|2010-06-05T03:46:29Z"
  "r23685bc_20120530_233021|2012-05-31T00:14:54Z|2012-05-31T00:58:44Z"
  "r23685bc_20140616_225022|2014-06-16T22:54:31Z|2014-06-16T23:32:19Z"
  "r29mrd5h_20090612_225306|2009-06-12T23:00:54Z|2009-06-13T00:45:53Z"
  "r29mrd5h_20110612_033752|2011-06-12T03:45:37Z|2011-06-12T04:23:43Z"
  "r29mrd5h_20130611_002419|2013-06-11T00:32:46Z|2013-06-11T01:08:39Z"
  "r7jjskxq_20101023_210332|2010-10-23T21:06:23Z|2010-10-23T21:51:50Z"
  "r7jjskxq_20121013_060425|2012-10-13T06:21:17Z|2012-10-13T07:02:50Z"
  "r7jjskxq_20131022_004934|2013-10-22T00:55:47Z|2013-10-22T01:32:58Z"
)

mkdir -p "${OUTPUT_DIR}"

cd "${REPO_ROOT}"

for range in "${DENSE_GRID_RANGES[@]}"; do
  IFS="|" read -r deployment_label start_time end_time <<< "${range}"

  input_file="${INPUT_DIR}/${deployment_label}_deployment_bundle.sqlite"
  output_file="${OUTPUT_DIR}/${deployment_label}_${LABEL_SUFFIX}_deployment_bundle.sqlite"

  uv run afft bundle clip \
    --input "${input_file}" \
    --output "${output_file}" \
    --start "${start_time}" \
    --end "${end_time}" \
    --label-suffix "${LABEL_SUFFIX}" \
    --no-clip "${NO_CLIP_PATTERN}" \
    --overwrite
done
