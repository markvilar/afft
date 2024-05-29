#!/usr/bin/bash

CAMERA_DIR="$HOME/data/acfr_revisits_processed/acfr_renav_cameras"
OUTPUT_DIR="$HOME/data/acfr_revisits_processed/acfr_cameras_prior"
LABEL_DIR="$HOME/data/acfr_revisits_processed/acfr_camera_labels"

echo "Uncomment exit command in script to execute batch processing"

exit 0

# Site 1 - qd61g27j

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qd61g27j_20100421_022145_cameras.csv" \
  "$OUTPUT_DIR/qd61g27j_20100421_022145_cameras.csv" \
  --labels "$LABEL_DIR/qd61g27j_20100421_022145_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qd61g27j_20110410_011202_cameras.csv" \
  "$OUTPUT_DIR/qd61g27j_20110410_011202_cameras.csv" \
  --labels "$LABEL_DIR/qd61g27j_20110410_011202_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qd61g27j_20120422_043114_cameras.csv" \
  "$OUTPUT_DIR/qd61g27j_20120422_043114_cameras.csv" \
  --labels "$LABEL_DIR/qd61g27j_20120422_043114_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qd61g27j_20130414_013620_cameras.csv" \
  "$OUTPUT_DIR/qd61g27j_20130414_013620_cameras.csv" \
  --labels "$LABEL_DIR/qd61g27j_20130414_013620_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qd61g27j_20170523_040815_cameras.csv" \
  "$OUTPUT_DIR/qd61g27j_20170523_040815_cameras.csv" \
  --labels "$LABEL_DIR/qd61g27j_20170523_040815_camera_labels.txt"


# Site 2 - qdc5ghs3

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdc5ghs3_20100430_024508_cameras.csv" \
  "$OUTPUT_DIR/qdc5ghs3_20100430_024508_cameras.csv" \
  --labels "$LABEL_DIR/qdc5ghs3_20100430_024508_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdc5ghs3_20120501_033336_cameras.csv" \
  "$OUTPUT_DIR/qdc5ghs3_20120501_033336_cameras.csv" \
  --labels "$LABEL_DIR/qdc5ghs3_20120501_033336_camera_labels.txt" 

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdc5ghs3_20130405_103429_cameras.csv" \
  "$OUTPUT_DIR/qdc5ghs3_20130405_103429_cameras.csv" \
  --labels "$LABEL_DIR/qdc5ghs3_20130405_103429_camera_labels.txt" 

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdc5ghs3_20210315_230947_cameras.csv" \
  "$OUTPUT_DIR/qdc5ghs3_20210315_230947_cameras.csv" \
  --labels "$LABEL_DIR/qdc5ghs3_20210315_230947_camera_labels.txt" 


# Site 3 - qdch0ftq

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20100428_020202_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20100428_020202_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20100428_020202_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20110415_020103_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20110415_020103_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20110415_020103_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20120430_002423_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20120430_002423_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20120430_002423_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20130406_023610_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20130406_023610_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20130406_023610_camera_labels.txt"

# NOTE: Troublesome file
poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20140327_071251_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20140327_071251_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20140327_071251_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20170526_025746_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20170526_025746_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20170526_025746_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdch0ftq_20210315_034028_cameras.csv" \
  "$OUTPUT_DIR/qdch0ftq_20210315_034028_cameras.csv" \
  --labels "$LABEL_DIR/qdch0ftq_20210315_034028_camera_labels.txt"


# Site 4 - qdchdmy1

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20110416_005411_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20110416_005411_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20110416_005411_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20120501_071203_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20120501_071203_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20120501_071203_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20130406_081713_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20130406_081713_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20130406_081713_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20140328_063358_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20140328_063358_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20140328_063358_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20170525_234624_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20170525_234624_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20170525_234624_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qdchdmy1_20210315_081519_cameras.csv" \
  "$OUTPUT_DIR/qdchdmy1_20210315_081519_cameras.csv" \
  --labels "$LABEL_DIR/qdchdmy1_20210315_081519_camera_labels.txt"


# Site 5 - qtqxshxs

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qtqxshxs_20110815_102540_cameras.csv" \
  "$OUTPUT_DIR/qtqxshxs_20110815_102540_cameras.csv" \
  --labels "$LABEL_DIR/qtqxshxs_20110815_102540_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qtqxshxs_20150327_015552_cameras.csv" \
  "$OUTPUT_DIR/qtqxshxs_20150327_015552_cameras.csv" \
  --labels "$LABEL_DIR/qtqxshxs_20150327_015552_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qtqxshxs_20150328_000850_cameras.csv" \
  "$OUTPUT_DIR/qtqxshxs_20150328_000850_cameras.csv" \
  --labels "$LABEL_DIR/qtqxshxs_20150328_000850_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/qtqxshxs_20150328_042551_cameras.csv" \
  "$OUTPUT_DIR/qtqxshxs_20150328_042551_cameras.csv" \
  --labels "$LABEL_DIR/qtqxshxs_20150328_042551_camera_labels.txt"


# Site 6 - r234xgje

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r234xgje_20100604_230524_cameras.csv" \
  "$OUTPUT_DIR/r234xgje_20100604_230524_cameras.csv" \
  --labels "$LABEL_DIR/r234xgje_20100604_230524_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r234xgje_20120530_064545_cameras.csv" \
  "$OUTPUT_DIR/r234xgje_20120530_064545_cameras.csv" \
  --labels "$LABEL_DIR/r234xgje_20120530_064545_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r234xgje_20140616_205232_cameras.csv" \
  "$OUTPUT_DIR/r234xgje_20140616_205232_cameras.csv" \
  --labels "$LABEL_DIR/r234xgje_20140616_205232_camera_labels.txt"


# Site 7 - r23685bc

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23685bc_20100605_021022_cameras.csv" \
  "$OUTPUT_DIR/r23685bc_20100605_021022_cameras.csv" \
  --labels "$LABEL_DIR/r23685bc_20100605_021022_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23685bc_20120530_233021_cameras.csv" \
  "$OUTPUT_DIR/r23685bc_20120530_233021_cameras.csv" \
  --labels "$LABEL_DIR/r23685bc_20120530_233021_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23685bc_20140616_225022_cameras.csv" \
  "$OUTPUT_DIR/r23685bc_20140616_225022_cameras.csv" \
  --labels "$LABEL_DIR/r23685bc_20140616_225022_camera_labels.txt"


# Site 8 - r23m7ms0

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23m7ms0_20100606_001908_cameras.csv" \
  "$OUTPUT_DIR/r23m7ms0_20100606_001908_cameras.csv" \
  --labels "$LABEL_DIR/r23m7ms0_20100606_001908_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23m7ms0_20120601_070118_cameras.csv" \
  "$OUTPUT_DIR/r23m7ms0_20120601_070118_cameras.csv" \
  --labels "$LABEL_DIR/r23m7ms0_20120601_070118_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r23m7ms0_20140616_044549_cameras.csv" \
  "$OUTPUT_DIR/r23m7ms0_20140616_044549_cameras.csv" \
  --labels "$LABEL_DIR/r23m7ms0_20140616_044549_camera_labels.txt"


# Site 9 - r29mrd12

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd12_20090613_010853_cameras.csv" \
  "$OUTPUT_DIR/r29mrd12_20090613_010853_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd12_20090613_010853_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd12_20090613_104954_cameras.csv" \
  "$OUTPUT_DIR/r29mrd12_20090613_104954_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd12_20090613_104954_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd12_20110612_045149_cameras.csv" \
  "$OUTPUT_DIR/r29mrd12_20110612_045149_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd12_20110612_045149_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd12_20130611_015335_cameras.csv" \
  "$OUTPUT_DIR/r29mrd12_20130611_015335_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd12_20130611_015335_camera_labels.txt"


# Site 10 - r29mrd5h

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd5h_20090612_225306_cameras.csv" \
  "$OUTPUT_DIR/r29mrd5h_20090612_225306_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd5h_20090612_225306_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd5h_20090613_100254_cameras.csv" \
  "$OUTPUT_DIR/r29mrd5h_20090613_100254_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd5h_20090613_100254_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd5h_20110612_033752_cameras.csv" \
  "$OUTPUT_DIR/r29mrd5h_20110612_033752_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd5h_20110612_033752_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r29mrd5h_20130611_002419_cameras.csv" \
  "$OUTPUT_DIR/r29mrd5h_20130611_002419_cameras.csv" \
  --labels "$LABEL_DIR/r29mrd5h_20130611_002419_camera_labels.txt"


# Site 11 - r7jjskxq

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjskxq_20101023_210332_cameras.csv" \
  "$OUTPUT_DIR/r7jjskxq_20101023_210332_cameras.csv" \
  --labels "$LABEL_DIR/r7jjskxq_20101023_210332_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjskxq_20121013_060425_cameras.csv" \
  "$OUTPUT_DIR/r7jjskxq_20121013_060425_cameras.csv" \
  --labels "$LABEL_DIR/r7jjskxq_20121013_060425_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjskxq_20131022_004934_cameras.csv" \
  "$OUTPUT_DIR/r7jjskxq_20131022_004934_cameras.csv" \
  --labels "$LABEL_DIR/r7jjskxq_20131022_004934_camera_labels.txt"


# Site 12 - r7jjss8n

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjss8n_20101023_210332_cameras.csv" \
  "$OUTPUT_DIR/r7jjss8n_20101023_210332_cameras.csv" \
  --labels "$LABEL_DIR/r7jjss8n_20101023_210332_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjss8n_20121013_060425_cameras.csv" \
  "$OUTPUT_DIR/r7jjss8n_20121013_060425_cameras.csv" \
  --labels "$LABEL_DIR/r7jjss8n_20121013_060425_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjss8n_20131022_004934_cameras.csv" \
  "$OUTPUT_DIR/r7jjss8n_20131022_004934_cameras.csv" \
  --labels "$LABEL_DIR/r7jjss8n_20131022_004934_camera_labels.txt"


# Site 13 - r7jjssbh

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjssbh_20101023_210332_cameras.csv" \
  "$OUTPUT_DIR/r7jjssbh_20101023_210332_cameras.csv" \
  --labels "$LABEL_DIR/r7jjssbh_20101023_210332_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjssbh_20121013_060425_cameras.csv" \
  "$OUTPUT_DIR/r7jjssbh_20121013_060425_cameras.csv" \
  --labels "$LABEL_DIR/r7jjssbh_20121013_060425_camera_labels.txt"

poetry run raft-cli filter-cameras \
  "$CAMERA_DIR/r7jjssbh_20131022_004934_cameras.csv" \
  "$OUTPUT_DIR/r7jjssbh_20131022_004934_cameras.csv" \
  --labels "$LABEL_DIR/r7jjssbh_20131022_004934_camera_labels.txt"

exit 0
