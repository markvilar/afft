#!/usr/bin/bash

set -e

SOURCE_DIR="/data/exos_01/acfr_messages_v4_processed"
OUTPUT_DIR="/data/exos_01/acfr_messages_v5_clipped"

TIMESTAMP_COLUMN="timestamp"
TIMESTAMP_FORMAT="ISO8601"

# --------------------------------------------------------------------------------------
# Site 1 - QDCH0FTQ
# --------------------------------------------------------------------------------------

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdch0ftq_20100428_020202_*" \
  --start "20100428_035439" \
  --end "20100428_043341"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdch0ftq_20110415_020103_*" \
  --start "20110415_034240" \
  --end "20110415_042034"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdch0ftq_20120430_002423_*" \
  --start "20120430_020721" \
  --end "20120430_024419"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdch0ftq_20130406_023610_*" \
  --start "20130406_050344" \
  --end "20130406_053938"


# --------------------------------------------------------------------------------------
# Site 2 - QDCHDMY1
# --------------------------------------------------------------------------------------

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdchdmy1_20110416_005411_*" \
  --start "20110416_005813" \
  --end "20110416_013709"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdchdmy1_20120501_071203_*" \
  --start "20120501_071514" \
  --end "20120501_075250"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdchdmy1_20130406_081713_*" \
  --start "20130406_082409" \
  --end "20130406_090032"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "qdchdmy1_20170525_234624_*" \
  --start "20170525_235945" \
  --end "20170526_003837"


# --------------------------------------------------------------------------------------
# Site 3 - R23685BC
# --------------------------------------------------------------------------------------

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r23685bc_20100605_021022_*" \
  --start "20100605_030040" \
  --end "20100605_034629"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r23685bc_20120530_233021_*" \
  --start "20120531_001454" \
  --end "20120531_005844"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r23685bc_20140616_225022_*" \
  --start "20140616_225431" \
  --end "20140616_233219"


# --------------------------------------------------------------------------------------
# Site 4 - R29MRD5H
# --------------------------------------------------------------------------------------

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r29mrd5h_20090612_225306_*" \
  --start "20090612_230054" \
  --end "20090613_004553"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r29mrd5h_20110612_033752_*" \
  --start "20110612_034537" \
  --end "20110612_042343"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r29mrd5h_20130611_002419_*" \
  --start "20130611_003246" \
  --end "20130611_010839"


# --------------------------------------------------------------------------------------
# Site 5 - R7JJSKXQ
# --------------------------------------------------------------------------------------

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r7jjskxq_20101023_210332_*" \
  --start "20101023_210623" \
  --end "20101023_215150"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r7jjskxq_20121013_060425_*" \
  --start "20121013_062117" \
  --end "20121013_070250"

uv run afft tasks clip-tables "${SOURCE_DIR}" "${OUTPUT_DIR}" \
  --timestamp-column "${TIMESTAMP_COLUMN}" \
  --timestamp-format "${TIMESTAMP_FORMAT}" \
  --pattern "r7jjskxq_20131022_004934_*" \
  --start "20131022_005547" \
  --end "20131022_013258"
