#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

TARGET="/test/notk-bot"

echo "Deploying to test"

cp -vf ${ROOT_DIR}/Release_Notes.md ${TARGET}/

cp -vf ${ROOT_DIR}/src/*.py ${TARGET}/

mkdir -p ${TARGET}/cfg/
cp -rvf ${ROOT_DIR}/cfg/test/* ${TARGET}/cfg/

echo "Deployed to test!"
