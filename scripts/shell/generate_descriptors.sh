#!/usr/bin/bash

DATA_DIRECTORY="/home/martin/data/acfr_revisits_unprocessed/acfr_measurements_unprocessed"
OUTPUT_DIRECTORY="/home/martin/data/acfr_revisits_processed/acfr_site_descriptors"

poetry run raft-cli describe "$DATA_DIRECTORY/qd61g27j" "$OUTPUT_DIRECTORY" --prefix qd61g27j
poetry run raft-cli describe "$DATA_DIRECTORY/qdc5ghs3" "$OUTPUT_DIRECTORY" --prefix qdc5ghs3
poetry run raft-cli describe "$DATA_DIRECTORY/qdch0ftq" "$OUTPUT_DIRECTORY" --prefix qdch0ftq
poetry run raft-cli describe "$DATA_DIRECTORY/qdchdmy1" "$OUTPUT_DIRECTORY" --prefix qdchdmy1
poetry run raft-cli describe "$DATA_DIRECTORY/qtqxshxs" "$OUTPUT_DIRECTORY" --prefix qtqxshxs
poetry run raft-cli describe "$DATA_DIRECTORY/r7jjskxq" "$OUTPUT_DIRECTORY" --prefix r7jjskxq
poetry run raft-cli describe "$DATA_DIRECTORY/r7jjss8n" "$OUTPUT_DIRECTORY" --prefix r7jjss8n
poetry run raft-cli describe "$DATA_DIRECTORY/r7jjssbh" "$OUTPUT_DIRECTORY" --prefix r7jjssbh
poetry run raft-cli describe "$DATA_DIRECTORY/r23m7ms0" "$OUTPUT_DIRECTORY" --prefix r23m7ms0
poetry run raft-cli describe "$DATA_DIRECTORY/r29mrd5h" "$OUTPUT_DIRECTORY" --prefix r29mrd5h
poetry run raft-cli describe "$DATA_DIRECTORY/r29mrd12" "$OUTPUT_DIRECTORY" --prefix r29mrd12
poetry run raft-cli describe "$DATA_DIRECTORY/r234xgje" "$OUTPUT_DIRECTORY" --prefix r234xgje
poetry run raft-cli describe "$DATA_DIRECTORY/r23685bc" "$OUTPUT_DIRECTORY" --prefix r23685bc

exit 0
