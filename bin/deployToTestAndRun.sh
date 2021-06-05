#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

set -e

${ROOT_DIR}/bin/deployToTest.bash
${ROOT_DIR}/bin/startServerTest.bash
