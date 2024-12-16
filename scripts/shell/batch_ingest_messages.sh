#!/usr/bin/bash

MESSAGE_DIR="/data/kingston_snv_01/acfr_messages_merged"
CONFIG="./config/protocol/protocol_v1.toml"

DATABASE="acfr_auv_messages"
HOST="localhost"
PORT=5432

ENABLE_QD61G27J=true
ENABLE_QDC5GHS3=true
ENABLE_QDCH0FTQ=true
ENABLE_QDCHDMY1=true
ENABLE_QTQXSHXS=true
ENABLE_R7JJSKXQ=true
ENABLE_R7JJSS8N=true
ENABLE_R7JJSSBH=true
ENABLE_R23M7MS0=true
ENABLE_R29MRD5H=true
ENABLE_R29MRD12=true
ENABLE_R234XGJE=true
ENABLE_R23685BC=true


# ------------------------------------------------------------------------------
# QD61G27J
# ------------------------------------------------------------------------------

if "${ENABLE_QD61G27J}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qd61g27j_20100421_022145_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qd61g27j_20100421_022145"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qd61g27j_20110410_011202_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qd61g27j_20110410_011202"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qd61g27j_20120422_043114_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qd61g27j_20120422_043114"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qd61g27j_20130414_013620_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qd61g27j_20130414_013620"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qd61g27j_20170523_040815_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qd61g27j_20170523_040815"

fi


# ------------------------------------------------------------------------------
# QDC5GHS3
# ------------------------------------------------------------------------------

if "${ENABLE_QDC5GHS3}"; then
  
  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdc5ghs3_20100430_024508_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdc5ghs3_20100430_024508"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdc5ghs3_20120501_033336_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdc5ghs3_20120501_033336"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdc5ghs3_20130405_103429_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdc5ghs3_20130405_103429"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdc5ghs3_20210315_230947_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdc5ghs3_20210315_230947"

fi


# ------------------------------------------------------------------------------
# QDCH0FTQ
# ------------------------------------------------------------------------------

if "${ENABLE_QDCH0FTQ}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20100428_020202_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20100428_020202"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20110415_020103_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20110415_020103"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20120430_002423_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20120430_002423"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20130406_023610_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20130406_023610"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20140327_071251_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20140327_071251"
   
  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20170526_025746_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20170526_025746"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdch0ftq_20210315_034028_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdch0ftq_20210315_034028"

fi


# ------------------------------------------------------------------------------
# QDCHDMY1
# ------------------------------------------------------------------------------

if "${ENABLE_QDCHDMY1}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20110416_005411_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20110416_005411"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20120501_071203_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20120501_071203"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20130406_081713_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20130406_081713"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20140328_063358_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20140328_063358"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20170525_234624_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20170525_234624"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qdchdmy1_20210315_081519_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qdchdmy1_20210315_081519"

fi


# ------------------------------------------------------------------------------
# QTQXSHXS
# ------------------------------------------------------------------------------

if "${ENABLE_QTQXSHXS}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qtqxshxs_20110815_102540_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qtqxshxs_20110815_102540"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qtqxshxs_20150327_015552_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qtqxshxs_20150327_015552"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qtqxshxs_20150328_000850_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qtqxshxs_20150328_000850"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/qtqxshxs_20150328_042551_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "qtqxshxs_20150328_042551"

fi


# ------------------------------------------------------------------------------
# R7JJSKXQ
# ------------------------------------------------------------------------------

if "${ENABLE_R7JJSKXQ}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjskxq_20101023_210332_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjskxq_20101023_210332"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjskxq_20121013_060425_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjskxq_20121013_060425"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjskxq_20131022_004934_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjskxq_20131022_004934"

fi


# ------------------------------------------------------------------------------
# R7JJSS8N
# ------------------------------------------------------------------------------

if "${ENABLE_R7JJSS8N}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjss8n_20101023_210332_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjss8n_20101023_210332"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjss8n_20121013_060425_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjss8n_20121013_060425"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjss8n_20131022_004934_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjss8n_20131022_004934"

fi


# ------------------------------------------------------------------------------
# R7JJSSBH
# ------------------------------------------------------------------------------

if "${ENABLE_R7JJSSBH}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjssbh_20101023_210332_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjssbh_20101023_210332"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjssbh_20121013_060425_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjssbh_20121013_060425"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r7jjssbh_20131022_004934_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r7jjssbh_20131022_004934"

fi


# ------------------------------------------------------------------------------
# R23M7MS0
# ------------------------------------------------------------------------------

if "${ENABLE_R23M7MS0}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23m7ms0_20100606_001908_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23m7ms0_20100606_001908"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23m7ms0_20120601_070118_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23m7ms0_20120601_070118"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23m7ms0_20140616_044549_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23m7ms0_20140616_044549"

fi


# ------------------------------------------------------------------------------
# R29MRD5H
# ------------------------------------------------------------------------------

if "${ENABLE_R29MRD5H}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd5h_20090612_225306_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd5h_20090612_225306"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd5h_20090613_100254_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd5h_20090613_100254"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd5h_20110612_033752_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd5h_20110612_033752"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd5h_20130611_002419_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd5h_20130611_002419"

fi


# ------------------------------------------------------------------------------
# R29MRD12
# ------------------------------------------------------------------------------

if "${ENABLE_R29MRD12}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd12_20090613_010853_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd12_20090613_010853"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd12_20090613_104954_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd12_20090613_104954"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd12_20110612_045149_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd12_20110612_045149"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r29mrd12_20130611_015335_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r29mrd12_20130611_015335"

fi


# ------------------------------------------------------------------------------
# R234XGJE
# ------------------------------------------------------------------------------

if "${ENABLE_R234XGJE}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r234xgje_20100604_230524_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r234xgje_20100604_230524"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r234xgje_20120530_064545_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r234xgje_20120530_064545"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r234xgje_20140616_205232_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r234xgje_20140616_205232"

fi


# ------------------------------------------------------------------------------
# R23685BC
# ------------------------------------------------------------------------------

if "${ENABLE_R23685BC}"; then

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23685bc_20100605_021022_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23685bc_20100605_021022"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23685bc_20120530_233021_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23685bc_20120530_233021"

  poetry run afft parse-messages \
    "${MESSAGE_DIR}/r23685bc_20140616_225022_messages.txt" \
    "${CONFIG}" \
    --database "${DATABASE}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --prefix "r23685bc_20140616_225022"

fi
