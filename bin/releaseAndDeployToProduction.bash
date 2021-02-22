#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

./release.bash $1

dryRun=0

if [ "$1" == "--dry-run" ]; then
    dryRun=1
fi

if [ $dryRun -eq 0 ]; then
    ./deployToProduction.bash
fi
