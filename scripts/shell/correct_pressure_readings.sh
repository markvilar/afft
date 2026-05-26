#!/usr/bin/bash

set -e

READINGS_DIR="/data/exos_01/acfr_messages_v2_parsed"
SEALEVEL_DIR="/data/exos_01/metocean_sea_level_hourly"
OUTPUT_DIR="/data/exos_01/acfr_messages_v3_metocean_corrected"

file_tuples=(
  # qd61g27j
  "qd61g27j_20100421_022145_pressure_parosci.csv" "qd61g27j_20090101_20211231_sea_level.csv" "qd61g27j_20100421_022145_pressure_parosci.csv"
  "qd61g27j_20110410_011202_pressure_parosci.csv" "qd61g27j_20090101_20211231_sea_level.csv" "qd61g27j_20110410_011202_pressure_parosci.csv"
  "qd61g27j_20120422_043114_pressure_parosci.csv" "qd61g27j_20090101_20211231_sea_level.csv" "qd61g27j_20120422_043114_pressure_parosci.csv"
  "qd61g27j_20130414_013620_pressure_parosci.csv" "qd61g27j_20090101_20211231_sea_level.csv" "qd61g27j_20130414_013620_pressure_parosci.csv"
  "qd61g27j_20170523_040815_pressure_parosci.csv" "qd61g27j_20090101_20211231_sea_level.csv" "qd61g27j_20170523_040815_pressure_parosci.csv"

  # qdc5ghs3
  "qdc5ghs3_20100430_024508_pressure_parosci.csv" "qdc5ghs3_20090101_20211231_sea_level.csv" "qdc5ghs3_20100430_024508_pressure_parosci.csv"
  "qdc5ghs3_20120501_033336_pressure_parosci.csv" "qdc5ghs3_20090101_20211231_sea_level.csv" "qdc5ghs3_20120501_033336_pressure_parosci.csv"
  "qdc5ghs3_20130405_103429_pressure_parosci.csv" "qdc5ghs3_20090101_20211231_sea_level.csv" "qdc5ghs3_20130405_103429_pressure_parosci.csv"
  "qdc5ghs3_20210315_230947_pressure_parosci.csv" "qdc5ghs3_20090101_20211231_sea_level.csv" "qdc5ghs3_20210315_230947_pressure_parosci.csv"

  # qdch0ftq
  "qdch0ftq_20100428_020202_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20100428_020202_pressure_parosci.csv"
  "qdch0ftq_20110415_020103_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20110415_020103_pressure_parosci.csv"
  "qdch0ftq_20120430_002423_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20120430_002423_pressure_parosci.csv"
  "qdch0ftq_20130406_023610_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20130406_023610_pressure_parosci.csv"
  "qdch0ftq_20140327_071251_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20140327_071251_pressure_parosci.csv"
  "qdch0ftq_20170526_025746_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20170526_025746_pressure_parosci.csv"
  "qdch0ftq_20210315_034028_pressure_parosci.csv" "qdch0ftq_20090101_20211231_sea_level.csv" "qdch0ftq_20210315_034028_pressure_parosci.csv"

  # qdchdmy1
  "qdchdmy1_20110416_005411_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20110416_005411_pressure_parosci.csv"
  "qdchdmy1_20120501_071203_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20120501_071203_pressure_parosci.csv"
  "qdchdmy1_20130406_081713_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20130406_081713_pressure_parosci.csv"
  "qdchdmy1_20140328_063358_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20140328_063358_pressure_parosci.csv"
  "qdchdmy1_20170525_234624_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20170525_234624_pressure_parosci.csv"
  "qdchdmy1_20210315_081519_pressure_parosci.csv" "qdchdmy1_20090101_20211231_sea_level.csv" "qdchdmy1_20210315_081519_pressure_parosci.csv"

  # qtqxshxs
  "qtqxshxs_20110815_102540_pressure_parosci.csv" "qtqxshxs_20090101_20211231_sea_level.csv" "qtqxshxs_20110815_102540_pressure_parosci.csv"
  "qtqxshxs_20150327_015552_pressure_parosci.csv" "qtqxshxs_20090101_20211231_sea_level.csv" "qtqxshxs_20150327_015552_pressure_parosci.csv"
  "qtqxshxs_20150328_000850_pressure_parosci.csv" "qtqxshxs_20090101_20211231_sea_level.csv" "qtqxshxs_20150328_000850_pressure_parosci.csv"
  "qtqxshxs_20150328_042551_pressure_parosci.csv" "qtqxshxs_20090101_20211231_sea_level.csv" "qtqxshxs_20150328_042551_pressure_parosci.csv"

  # r234xgje
  "r234xgje_20100604_230524_pressure_parosci.csv" "r234xgje_20090101_20211231_sea_level.csv" "r234xgje_20100604_230524_pressure_parosci.csv"
  "r234xgje_20120530_064545_pressure_parosci.csv" "r234xgje_20090101_20211231_sea_level.csv" "r234xgje_20120530_064545_pressure_parosci.csv"
  "r234xgje_20140616_205232_pressure_parosci.csv" "r234xgje_20090101_20211231_sea_level.csv" "r234xgje_20140616_205232_pressure_parosci.csv"

  # r23685bc
  "r23685bc_20100605_021022_pressure_parosci.csv" "r23685bc_20090101_20211231_sea_level.csv" "r23685bc_20100605_021022_pressure_parosci.csv"
  "r23685bc_20120530_233021_pressure_parosci.csv" "r23685bc_20090101_20211231_sea_level.csv" "r23685bc_20120530_233021_pressure_parosci.csv"
  "r23685bc_20140616_225022_pressure_parosci.csv" "r23685bc_20090101_20211231_sea_level.csv" "r23685bc_20140616_225022_pressure_parosci.csv"

  # r23m7ms0
  "r23m7ms0_20100606_001908_pressure_parosci.csv" "r23m7ms0_20090101_20211231_sea_level.csv" "r23m7ms0_20100606_001908_pressure_parosci.csv"
  "r23m7ms0_20120601_070118_pressure_parosci.csv" "r23m7ms0_20090101_20211231_sea_level.csv" "r23m7ms0_20120601_070118_pressure_parosci.csv"
  "r23m7ms0_20140616_044549_pressure_parosci.csv" "r23m7ms0_20090101_20211231_sea_level.csv" "r23m7ms0_20140616_044549_pressure_parosci.csv"

  # r29mrd12
  "r29mrd12_20090613_010853_pressure_parosci.csv" "r29mrd12_20090101_20211231_sea_level.csv" "r29mrd12_20090613_010853_pressure_parosci.csv"
  "r29mrd12_20090613_104954_pressure_parosci.csv" "r29mrd12_20090101_20211231_sea_level.csv" "r29mrd12_20090613_104954_pressure_parosci.csv"
  "r29mrd12_20110612_045149_pressure_parosci.csv" "r29mrd12_20090101_20211231_sea_level.csv" "r29mrd12_20110612_045149_pressure_parosci.csv"
  "r29mrd12_20130611_015335_pressure_parosci.csv" "r29mrd12_20090101_20211231_sea_level.csv" "r29mrd12_20130611_015335_pressure_parosci.csv"

  # r29mrd5h
  "r29mrd5h_20090612_225306_pressure_parosci.csv" "r29mrd5h_20090101_20211231_sea_level.csv" "r29mrd5h_20090612_225306_pressure_parosci.csv"
  "r29mrd5h_20090613_100254_pressure_parosci.csv" "r29mrd5h_20090101_20211231_sea_level.csv" "r29mrd5h_20090613_100254_pressure_parosci.csv"
  "r29mrd5h_20110612_033752_pressure_parosci.csv" "r29mrd5h_20090101_20211231_sea_level.csv" "r29mrd5h_20110612_033752_pressure_parosci.csv"
  "r29mrd5h_20130611_002419_pressure_parosci.csv" "r29mrd5h_20090101_20211231_sea_level.csv" "r29mrd5h_20130611_002419_pressure_parosci.csv"

  # r7jjskxq
  "r7jjskxq_20101023_210332_pressure_parosci.csv" "r7jjskxq_20090101_20211231_sea_level.csv" "r7jjskxq_20101023_210332_pressure_parosci.csv"
  "r7jjskxq_20121013_060425_pressure_parosci.csv" "r7jjskxq_20090101_20211231_sea_level.csv" "r7jjskxq_20121013_060425_pressure_parosci.csv"
  "r7jjskxq_20131022_004934_pressure_parosci.csv" "r7jjskxq_20090101_20211231_sea_level.csv" "r7jjskxq_20131022_004934_pressure_parosci.csv"

  # r7jjss8n
  "r7jjss8n_20101023_210332_pressure_parosci.csv" "r7jjss8n_20090101_20211231_sea_level.csv" "r7jjss8n_20101023_210332_pressure_parosci.csv"
  "r7jjss8n_20121013_060425_pressure_parosci.csv" "r7jjss8n_20090101_20211231_sea_level.csv" "r7jjss8n_20121013_060425_pressure_parosci.csv"
  "r7jjss8n_20131022_004934_pressure_parosci.csv" "r7jjss8n_20090101_20211231_sea_level.csv" "r7jjss8n_20131022_004934_pressure_parosci.csv"

  # r7jjssbh
  "r7jjssbh_20101023_210332_pressure_parosci.csv" "r7jjssbh_20090101_20211231_sea_level.csv" "r7jjssbh_20101023_210332_pressure_parosci.csv"
  "r7jjssbh_20121013_060425_pressure_parosci.csv" "r7jjssbh_20090101_20211231_sea_level.csv" "r7jjssbh_20121013_060425_pressure_parosci.csv"
  "r7jjssbh_20131022_004934_pressure_parosci.csv" "r7jjssbh_20090101_20211231_sea_level.csv" "r7jjssbh_20131022_004934_pressure_parosci.csv"
)


for ((i=0; i<${#file_tuples[@]}; i+=3)); do
  readings_file="${file_tuples[i]}"
  sealevel_file="${file_tuples[i+1]}"
  output_file="${file_tuples[i+2]}"

  readings_path="${READINGS_DIR}/${readings_file}"
  sealevel_path="${SEALEVEL_DIR}/${sealevel_file}"
  output_path="${OUTPUT_DIR}/${output_file}"

  uv run afft tasks correct-pressure-tide "${readings_path}" "${sealevel_path}" "${output_path}"
done
