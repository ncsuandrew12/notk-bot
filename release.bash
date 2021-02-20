#!/bin/bash

set -e

if [[ `git status --short | wc -l` -ne 0 ]]; then
    >&2 echo "ERROR: Uncommitted files."
    exit 1
fi;

git push

latestVersion=`git tag --list | grep alpha | sed s'/alpha-//g' | sed -r 's/\.([0-9])$/.0\1/g' | sed -r 's/\.([0-9][0-9])$/.0\1/g' | sort | tail -1`
latestMajor=$(sed s'/\.[^.]*$//' <<< $latestVersion)
latestMinor=$(sed s'/[^.]*\.//' <<< $latestVersion)

minor=$((latestMinor+1))

newVersion="${latestMajor}.${minor}"

tagLabel="${newVersion}"

if [ $latestMajor -eq 0 ]; then
    tagLabel="alpha-$tagLabel"
fi

git tag -a "$tagLabel" -m "Tagging $tagLabel"

git push --tags

./update_bot_host.bash