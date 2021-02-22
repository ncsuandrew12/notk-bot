#!/bin/bash

set -e

./release.bash $1

dryRun=0

if [ "$1" == "--dry-run" ]; then
    dryRun=1
fi

if [ $dryRun -eq 0 ]; then
    ./deployToProduction.bash
fi
