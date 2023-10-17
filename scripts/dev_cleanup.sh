#!/usr/bin/bash

CONFIG_FILE=./config/copy_scr_01.ini
pipenv run cleanup --config ${CONFIG_FILE} --dry-run
