#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

TARGET="/production/notk-bot"

tag=`git tag --points-at HEAD`

if [[ `echo "$tag" | wc -w` -eq 0 ]]; then
    >&2 echo "ERROR: The current commit is not tagged."
    exit 1
fi

echo "Deploying to production"

cp -vf ${ROOT_DIR}/src/main.py ${TARGET}/

mkdir -p ${TARGET}/cfg/
cp -rvf ${ROOT_DIR}/cfg/production/* ${TARGET}/cfg/

echo "Deployed to production!"