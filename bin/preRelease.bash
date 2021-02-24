#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

cd "${ROOT_DIR}"

lastTag=`git describe --abbrev=0`
commitHistory=`git log --pretty=oneline ${lastTag}..HEAD | sed -r 's/^[^ ]+ /-/'`

echo "Release commit history:"
echo -e "$commitHistory"

echo -e "$commitHistory" >> RELEASE_NOTES
