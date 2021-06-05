#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

dryRun=0

args=$@

while (( "$#" )); do
    case "$1" in
        -d|--dry-run)
            dryRun=1
            shift
            ;;
        --major-release)
            shift
            ;;
        --minor-release)
            shift
            ;;
        -*|--*=) # unsupported flags
            >&2 echo "ERROR: Unsupported parameter $1"
            exit $ERR_BAD_PARAMETER
            ;;
        *) # preserve positional arguments
            >&2 echo "ERROR: Unexpected argument $1"
            exit ${ERR_BAD_ARGUMENT}
            ;;
    esac
done

${ROOT_DIR}/bin/createRelease.bash "$args"

if [ $dryRun -eq 0 ]; then
    ${ROOT_DIR}/bin/deployToProduction.bash

    ${ROOT_DIR}/bin/startServerProduction.bash
fi
