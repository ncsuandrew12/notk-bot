#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

${ROOT_DIR}/bin/test.bash

${ROOT_DIR}/bin/releaseToProduction.bash "$@"
