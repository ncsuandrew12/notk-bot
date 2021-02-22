#!/bin/bash

set -e

dryRun=0

if [ "$1" == "--dry-run" ]; then
    dryRun=1
fi

if [[ `git status --short | wc -l` -ne 0 ]]; then
    >&2 echo "ERROR: Uncommitted files:"
    git status
    exit 1
fi;

if [ $dryRun -eq 0 ]; then
    echo "Pushing changes."
    git push
fi

major=0
minor=1;
if [ `git tag --list | wc -l` -gt 0 ]; then
    latestVersion=`git tag --list | sed -r 's/\.([0-9])$/.0\1/g' | sed -r 's/\.([0-9][0-9])$/.0\1/g' | sort | tail -1`
    latestMajor=$(sed s'/\.[^.]*$//' <<< $latestVersion)
    latestMinor=$(sed s'/[^.]*\.//' <<< $latestVersion)
    latestMajor=$(sed -r 's/^0+([0-9])/\1/' <<< $latestMajor)
    latestMinor=$(sed -r 's/^0+([0-9])/\1/' <<< $latestMinor)

    major=$((latestMajor))
    minor=$((latestMinor+1))
fi;

newVersion="${major}.${minor}"

tagLabel="${newVersion}"

read -p "Release $tagLabel? [y/N]: " doRelease
doRelease=$(tr '[:upper:]' '[:lower:]' <<< $doRelease)
if [[ "$doRelease" != "y" ]]; then
    >&2 echo "Release cancelled!"
    exit 2
fi
if [ $dryRun -eq 0 ]; then
    git tag -a "$tagLabel" -m "Tagging $tagLabel"

    echo "Pushing tags."
    git push --tags
fi
