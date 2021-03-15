#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

${ROOT_DIR}/bin/deploy.bash test

deploymentJson=$(jq -r ".test" ${ROOT_DIR}/bin/config.json)
targetDir=/home/`whoami`/$(jq -r ".dir" <<< $deploymentJson)

cd ${targetDir}

python3 -m unittest discover -fv -s ${targetDir} -p "*Test.py"
