#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

dryRun=0

while (( "$#" )); do
    case "$1" in
        -d|--dry-run)
            dryRun=1
            shift
            ;;
        -*|--*=) # unsupported flags
            >&2 echo "ERROR: Unsupported parameter $1"
            exit 1
            ;;
        *) # preserve positional arguments
            >&2 echo "ERROR: Unexpected argument $1"
            exit 2
            ;;
    esac
done

./release.bash "$@"

if [ $dryRun -eq 0 ]; then
    ./deployToProduction.bash
fi
