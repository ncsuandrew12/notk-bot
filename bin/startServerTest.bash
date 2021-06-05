#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/common.bash

set -e

echo "Starting server!"

cd /home/`whoami`/$(jq -r ".dir" ${ROOT_DIR}/cfg/test/deploy.json)

python3 main.py

echo "Server exited!"
