#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

set -e

pwd
./deployToTest.bash

cd /test/notk-bot

python3 main.py
