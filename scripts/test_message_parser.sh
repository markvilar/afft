#!/usr/bin/bash

#pipenv run process_messages \
#  config/data/r23685bc/20100605_messages.toml \
#  config/protocol/protocol_v1.toml

pipenv run process_messages \
  config/data/r23685bc/20120530_messages.toml \
  config/protocol/protocol_v1.toml

#pipenv run process_messages \
#  config/data/r23685bc/20140530_messages.toml \
#  config/protocol/protocol_v1.toml
