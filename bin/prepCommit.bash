#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

set -x

cd ${ROOT_DIR}

git add *
git add .gitignore

set -e

git diff --cached > diff.diff

git status
