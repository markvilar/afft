#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../../config"

SOURCE_DIR="/data/exos_01/acfr_messages_v2_parsed"
OUTPUT_DIR="/data/exos_01/acfr_messages_v4_telemetry_processed"

# --------------------------------------------------------------------------------------
# Site 1
# --------------------------------------------------------------------------------------

# NOTE: Test USBL processing
uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20100428_020202_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20100428_020202_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20100428_020202_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20100428_020202"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20100428_020202_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20100428_020202_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20100428_020202_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20100428_020202" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20110415_020103_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20110415_020103_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20110415_020103_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20110415_020103"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20110415_020103_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20110415_020103_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20110415_020103_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20110415_020103" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20120430_002423_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20120430_002423_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20120430_002423_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20120430_002423"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20120430_002423_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20120430_002423_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20120430_002423_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20120430_002423" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20130406_023610_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20130406_023610_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20130406_023610_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20130406_023610"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20130406_023610_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdch0ftq_20130406_023610_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20130406_023610_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20130406_023610" \
  --ignore-extrinsics

# --------------------------------------------------------------------------------------
# Site 2
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20110416_005411_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20110416_005411_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20110416_005411_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20110416_005411"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20110416_005411_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20110416_005411_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20110416_005411_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20110416_005411" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20120501_071203_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20120501_071203_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20120501_071203_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20120501_071203"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20120501_071203_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20120501_071203_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20120501_071203_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20120501_071203" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20130406_081713_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20130406_081713_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20130406_081713_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20130406_081713"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20130406_081713_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/qdchdmy1_20130406_081713_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20130406_081713_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20130406_081713" \
  --ignore-extrinsics

# --------------------------------------------------------------------------------------
# Site 3
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20100605_021022_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20100605_021022_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20100605_021022_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20100605_021022"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20100605_021022_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20100605_021022_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20100605_021022_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20100605_021022" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20120530_233021_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20120530_233021_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20120530_233021_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20120530_233021"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20120530_233021_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20120530_233021_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20120530_233021_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20120530_233021" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20140616_225022_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20140616_225022_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20140616_225022_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20140616_225022"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r23685bc_20140616_225022_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r23685bc_20140616_225022_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20140616_225022_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20140616_225022" \
  --ignore-extrinsics

# --------------------------------------------------------------------------------------
# Site 4
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20090612_225306_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20090612_225306_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20090612_225306_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20090612_225306"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20090612_225306_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20090612_225306_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20090612_225306_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20090612_225306" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20110612_033752_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20110612_033752_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20110612_033752_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20110612_033752"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20110612_033752_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20110612_033752_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20110612_033752_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20110612_033752" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20130611_002419_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20130611_002419_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20130611_002419_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20130611_002419"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20130611_002419_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r29mrd5h_20130611_002419_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20130611_002419_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20130611_002419" \
  --ignore-extrinsics

# --------------------------------------------------------------------------------------
# Site 5
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20101023_210332_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20101023_210332_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20101023_210332_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20101023_210332"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20101023_210332_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20101023_210332_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20101023_210332_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20101023_210332" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20121013_060425_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20121013_060425_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20121013_060425_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20121013_060425"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20121013_060425_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20121013_060425_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20121013_060425_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20121013_060425" \
  --ignore-extrinsics

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20131022_004934_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20131022_004934_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20131022_004934_usbl_tracklink_with_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20131022_004934"

uv run afft sensors process-tracklink-usbl-from-messages \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20131022_004934_usbl_tracklink.csv" \
  --pressure-file "${SOURCE_DIR}/r7jjskxq_20131022_004934_pressure_parosci.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20131022_004934_usbl_tracklink_without_extrinsics.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20131022_004934" \
  --ignore-extrinsics

