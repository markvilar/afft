#!/usr/bin/bash

SRC_ROOT="/lizard_island/reef_records/island_new"
DST_ROOT="/data/seagate_barracuda/lizard_island_test_sites"

SRC_HOST="st_andrews"

YEAR="2022_11"
SITE="horseshoe"

IMAGE_PATTERN="images*/**"
METASHAPE_PATTERN="metashape_files/**"

declare -a YEARS=(
  "2023_11"
  "2022_11"
  "2021_03"
  "2019_11"
  "2018_11"
  "2017_11"
  "2016_11"
  "2015_11"
  "2015_05"
  "2014_10"
  "2014_04"
)

for YEAR in "${YEARS[@]}"
do

  echo "Transferring deployment ${YEAR} for site ${SITE}"

  rclone copy "${SRC_HOST}:${SRC_ROOT}/${YEAR}/${SITE}" \
    "${DST_ROOT}/${YEAR}_${SITE}" \
    --include "${IMAGE_PATTERN}" \
    --include "${METASHAPE_PATTERN}"

done



