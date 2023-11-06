#!/usr/bin/bash

pipenv run cleanup --config ./config/copy_scr_01.ini
pipenv run cleanup --config ./config/copy_seq_01.ini
pipenv run cleanup --config ./config/copy_tas_01.ini
pipenv run cleanup --config ./config/copy_tas_02.ini
pipenv run cleanup --config ./config/copy_was_01.ini
pipenv run cleanup --config ./config/copy_was_02.ini
pipenv run cleanup --config ./config/copy_was_03.ini
