#!/usr/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../../config"

SOURCE_DIR="/data/exos_01/acfr_tracklink_logs_v2_parsed"
OUTPUT_DIR="/data/exos_01/acfr_tracklink_logs_v3_resolved"

# --------------------------------------------------------------------------------------
# qd61g27j
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qd61g27j_20100421_022145_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qd61g27j_20100421_022145_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qd61g27j_20100421_022145"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qd61g27j_20110410_011202_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qd61g27j_20110410_011202_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qd61g27j_20110410_011202"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qd61g27j_20120422_043114_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qd61g27j_20120422_043114_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qd61g27j_20120422_043114"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qd61g27j_20130414_013620_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qd61g27j_20130414_013620_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qd61g27j_20130414_013620"

# --------------------------------------------------------------------------------------
# qdc5ghs3
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdc5ghs3_20100430_024508_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdc5ghs3_20100430_024508_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qdc5ghs3_20100430_024508"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdc5ghs3_20120501_033336_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdc5ghs3_20120501_033336_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qdc5ghs3_20120501_033336"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdc5ghs3_20130405_103429_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdc5ghs3_20130405_103429_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qdc5ghs3_20130405_103429"

# --------------------------------------------------------------------------------------
# qdch0ftq
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20100428_020202_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20100428_020202_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20100428_020202"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20110415_020103_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20110415_020103_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20110415_020103"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20120430_002423_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20120430_002423_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20120430_002423"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20130406_023610_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20130406_023610_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20130406_023610"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdch0ftq_20140327_071251_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdch0ftq_20140327_071251_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdch0ftq_20140327_071251"

# --------------------------------------------------------------------------------------
# qdchdmy1
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20110416_005411_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20110416_005411_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20110416_005411"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20130406_081713_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20130406_081713_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20130406_081713"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qdchdmy1_20140328_063358_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qdchdmy1_20140328_063358_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "qdchdmy1_20140328_063358"

# --------------------------------------------------------------------------------------
# qtqxshxs
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/qtqxshxs_20110815_102540_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/qtqxshxs_20110815_102540_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "qtqxshxs_20110815_102540"

# --------------------------------------------------------------------------------------
# r234xgje
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r234xgje_20100604_230524_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r234xgje_20100604_230524_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r234xgje_20100604_230524"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r234xgje_20120530_064545_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r234xgje_20120530_064545_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r234xgje_20120530_064545"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r234xgje_20140616_205232_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r234xgje_20140616_205232_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r234xgje_20140616_205232"

# --------------------------------------------------------------------------------------
# r23685bc
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23685bc_20100605_021022_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20100605_021022_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20100605_021022"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23685bc_20120530_233021_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20120530_233021_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20120530_233021"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23685bc_20140616_225022_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23685bc_20140616_225022_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r23685bc_20140616_225022"

# --------------------------------------------------------------------------------------
# r23m7ms0
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23m7ms0_20100606_001908_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23m7ms0_20100606_001908_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r23m7ms0_20100606_001908"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23m7ms0_20120601_070118_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23m7ms0_20120601_070118_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r23m7ms0_20120601_070118"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r23m7ms0_20140616_044549_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r23m7ms0_20140616_044549_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r23m7ms0_20140616_044549"

# --------------------------------------------------------------------------------------
# r29mrd12
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd12_20090613_010853_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd12_20090613_010853_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r29mrd12_20090613_010853"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd12_20090613_104954_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd12_20090613_104954_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r29mrd12_20090613_104954"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd12_20110612_045149_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd12_20110612_045149_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r29mrd12_20110612_045149"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd12_20130611_015335_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd12_20130611_015335_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r29mrd12_20130611_015335"

# --------------------------------------------------------------------------------------
# r29mrd5h
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20090612_225306_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20090612_225306_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20090612_225306"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20090613_100254_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20090613_100254_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20090613_100254"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20110612_033752_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20110612_033752_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20110612_033752"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r29mrd5h_20130611_002419_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r29mrd5h_20130611_002419_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r29mrd5h_20130611_002419"

# --------------------------------------------------------------------------------------
# r7jjskxq
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20101023_210332_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20101023_210332_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20101023_210332"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20121013_060425_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20121013_060425_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20121013_060425"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjskxq_20131022_004934_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjskxq_20131022_004934_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_selected.toml" \
  --deployment "r7jjskxq_20131022_004934"

# --------------------------------------------------------------------------------------
# r7jjss8n
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjss8n_20101023_210332_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjss8n_20101023_210332_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjss8n_20101023_210332"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjss8n_20121013_060425_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjss8n_20121013_060425_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjss8n_20121013_060425"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjss8n_20131022_004934_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjss8n_20131022_004934_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjss8n_20131022_004934"

# --------------------------------------------------------------------------------------
# r7jjssbh
# --------------------------------------------------------------------------------------

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjssbh_20101023_210332_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjssbh_20101023_210332_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjssbh_20101023_210332"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjssbh_20121013_060425_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjssbh_20121013_060425_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjssbh_20121013_060425"

uv run afft sensors process-tracklink-usbl-from-logs \
  --usbl-file "${SOURCE_DIR}/r7jjssbh_20131022_004934_tracklink_fixes.csv" \
  --output-file "${OUTPUT_DIR}/r7jjssbh_20131022_004934_tracklink_fixes.csv" \
  --deployment-configs "${CONFIG_DIR}/deployment_configs_all.toml" \
  --deployment "r7jjssbh_20131022_004934"
